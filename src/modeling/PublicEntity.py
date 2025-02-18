import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List, Set
from modeling.sec_edgar.efts.query import QueryHit
from modeling.sec_edgar.submissions.SubmissionsResponse import SubmissionsResponse
import logging

from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from modeling.filing.SEC_Filing import SEC_Filing
from modeling.filing.SEC_Form_Types import SEC_Form_Types

from services.ai.bitcoin_events import *
from services.ai.events_transformer import *
from modeling.filing.Bitcoin_Filing import Bitcoin_Filing


class PublicEntity(BaseModel):
    # Necessary fields
    name: str = Field(..., description="The full legal name of the company.")
    ticker: Optional[str] = Field(
        None, description="The stock ticker symbol of the company, if applicable."
    )
    cik: str = Field(
        ..., description="The Central Index Key (CIK) assigned by the SEC."
    )
    # Optional fields
    entity_type: str = Field(default=None, description="The type of entity.")
    sic: str = Field(
        default=None, description="The Standard Industrial Classification code."
    )
    sicDescription: str = Field(
        default=None, description="The description of the SIC code."
    )
    website: Optional[str] = Field(default=None, description="The company's website.")
    exchanges: List[str] = Field(
        default=[], description="The stock exchanges the company is listed on."
    )
    category: Optional[str] = Field(
        default=None, description="The category of the company."
    )
    phone: str = Field(default=None, description="The company's phone number.")

    # List of EFTS query results for this entity
    accepted_bitcoin_filing_types: List[SEC_Form_Types] = Field(
        default=[
            SEC_Form_Types.FORM_8K

        ],
        description="The list of accepted filing types for bitcoin filings.",
    )
    bitcoin_filings: List[Bitcoin_Filing] = Field(
        default=[],
        description="The list of Bitcoin filings, containing the word bitcoin for this entity,",
    )
    filing_metadatas: List[SEC_Filing_Metadata] = Field(
        default=[], description="The list of submissions for this entity."
    )

    # Initializers

    @classmethod
    async def from_cik(cls, cik: str) -> "PublicEntity":
        from services.edgar import retrieve_submissions_for_entity_async

        logger = logging.getLogger(cls.__name__)

        # zfill cik
        cik = str(cik).zfill(10)
        submission_response = await retrieve_submissions_for_entity_async(cik)
        # Extract necessary fields
        name = submission_response["name"]
        ticker = (
            submission_response["tickers"][0]
            if submission_response["tickers"]
            else None
        )

        # Extract optional fields
        entity_type = submission_response.get("entityType")
        sic = submission_response.get("sic")
        sic_description = submission_response.get("sicDescription")
        website = submission_response.get("website")
        exchanges = submission_response.get("exchanges")
        category = submission_response.get("category")
        phone = submission_response.get("phone")

        # Extract recent filings
        filing_metadatas = SubmissionsResponse.from_dict(
            submission_response
        ).filing_metadatas

        public_entity = cls(
            name=name,
            ticker=ticker,
            cik=cik,
            entity_type=entity_type,
            sic=sic,
            sicDescription=sic_description,
            website=website,
            exchanges=exchanges,
            category=category,
            phone=phone,
            filing_metadatas=filing_metadatas,
        )
        logger.info(
            f"Retrieved public entity {public_entity.name} with ticker {public_entity.ticker} and entity type {public_entity.entity_type}"
        )

        return public_entity

    @classmethod
    async def from_ciks(cls, ciks: Set[str]) -> List["PublicEntity"]:
        logger = logging.getLogger(cls.__name__)
        entities = []

        async def fetch_entity(cik):
            return await cls.from_cik(cik)

        tasks = []
        for cik in ciks:
            tasks.append(fetch_entity(cik))
            if len(tasks) == 10:
                entities.extend(await asyncio.gather(*tasks))
                tasks = []
                await asyncio.sleep(1)  # Wait for 1 second to adhere to rate limit

        if tasks:
            entities.extend(await asyncio.gather(*tasks))

        return entities

    # Getters

    def get_filing_metadatas(self) -> List[SEC_Filing_Metadata]:
        return self.filing_metadatas

    def _get_filing_metadata(
        self, accession_number: str
    ) -> Optional[SEC_Filing_Metadata]:
        for filing_metadata in self.filing_metadatas:
            if filing_metadata.accession_number == accession_number:
                return filing_metadata
        return None

    # Updaters

    async def load_new_bitcoin_filings(self) -> "PublicEntity":
        
        from modeling.sec_edgar.efts.query import Base_Bitcoin_Query
        from services.edgar import get_query_result_async
        
        # Logger
        logger = logging.getLogger(self.__class__.__name__)

        # Retrieve QueryResult (QueryHits) for bitcoin query (keyword "bitcoin")
        base_bitcoin_query = Base_Bitcoin_Query(ciks=self.cik).model_dump(
            exclude_none=True
        )
        query_result = await get_query_result_async(q=base_bitcoin_query)
        bitcoin_filing_hits = query_result.hits
        # Only store hits with form type 8-K, 10-Q or 10-K
        filtered_bitcoin_filing_hits = [
            hit
            for hit in bitcoin_filing_hits
            if hit.form_type in self.accepted_bitcoin_filing_types
        ]
        
        # Convert QueryHits to Bitcoin_Filings
        all_bitcoin_filings = [ Bitcoin_Filing.from_query_hit(hit) for hit in filtered_bitcoin_filing_hits]
        
        # Filter out filings that are already stored
        new_bitcoin_filings = [
            filing
            for filing in all_bitcoin_filings
            if filing.url
            not in [bf.url for bf in self.bitcoin_filings]
        ]
        
        # Load the html content for the new bitcoin filings
        new_bitcoin_filings_w_content = await Bitcoin_Filing.load_html_content_for(new_bitcoin_filings)
        
        # Extract the bitcoin events for the new bitcoin filings (adhere to rate limit)
        new_bitcoin_filings_w_events = await Bitcoin_Filing.extract_bitcoin_events_for(new_bitcoin_filings_w_content)
        
        # Parse the extracted events into Bitcoin treasury statuses
        new_bitcoin_filings_w_treasury_stats = await Bitcoin_Filing.parse_bitcoin_events_for(new_bitcoin_filings_w_events)
        
        # Remove the raw text from the bitcoin filing to save space in the database
        for filing in new_bitcoin_filings_w_treasury_stats:
            filing.raw_text = ""
        
        # Add the new bitcoin filings to the entity
        self.bitcoin_filings.extend(new_bitcoin_filings_w_treasury_stats)
        logger.info(
            f"Added {len(new_bitcoin_filings)} new Bitcoin filings to entity {self.name}"
        )
        
        return self
    
    def get_bitcoin_treasury_updates(self) -> List[BitcoinTreasuryUpdate]:
        return [
            filing.bitcoin_treasury_update
            for filing in self.bitcoin_filings
            if filing.has_total_bitcoin_holdings
        ]
    
    def get_bitcoin_total_holdings_statements(self) -> List[TotalBitcoinHoldings]:
        return [ filing.total_bitcoin_holdings for filing in self.bitcoin_filings if filing.has_total_bitcoin_holdings]
    
    
    def get_btc_amt_in_treasury(self) -> float:
        # Return the latest and most accurate bitcoin holdings
        for filing in sorted(self.bitcoin_filings, key=lambda x: datetime.fromisoformat(x.file_date), reverse=True):
            if filing.has_total_bitcoin_holdings:
                return filing.total_bitcoin_holdings.total_bitcoin_holdings
        return 0.0