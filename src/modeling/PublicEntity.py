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

from services.ai.bitcoin_update import *
from services.ai.chain_of_thought import *


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
            SEC_Form_Types.FORM_8K,
            SEC_Form_Types.FORM_10Q,
            SEC_Form_Types.FORM_10K,
        ],
        description="The list of accepted filing types for bitcoin filings.",
    )
    bitcoin_filing_hits: List[QueryHit] = Field(
        default=[],
        description="The list of EFTS hits, containing the word bitcoin for this entity,",
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

    async def update_bitcoin_filing_hits(self) -> "PublicEntity":
        from modeling.sec_edgar.efts.query import Base_Bitcoin_Query
        from services.edgar import get_query_result_async

        # Retrieve QueryResult (QueryHits) for bitcoin query (keyword "bitcoin")
        base_bitcoin_query = Base_Bitcoin_Query(ciks=self.cik).model_dump(
            exclude_none=True
        )
        logging.info(base_bitcoin_query)
        query_result = await get_query_result_async(q=base_bitcoin_query)
        bitcoin_filing_hits = query_result.hits
        # Only store hits with form type 8-K, 10-Q or 10-K
        filtered_bitcoin_filing_hits = [
            hit
            for hit in bitcoin_filing_hits
            if hit.form_type in self.accepted_bitcoin_filing_types
        ]
        self.bitcoin_filing_hits = filtered_bitcoin_filing_hits

        # Extract events for first filing
        filings_ex99 = [
            hit
            for hit in filtered_bitcoin_filing_hits
            if (hit.form_type == "8-K" and hit.file_type == "EX-99.1")
        ]
        bitcoin_update_extractor = BitcoinTreasuryUpdateExtractor()
        metadatas = sorted(
            [self._get_filing_metadata(hit.accession_number) for hit in filings_ex99],
            key=lambda metadata: (
                datetime.strptime(metadata.filing_date, "%Y-%m-%d")
                if metadata and metadata.filing_date
                else datetime.min
            ),
        )

        logging.info(metadatas)

        for i, metadata in enumerate(metadatas):
            metadata.document_url = filings_ex99[i].url

        # metadata.document_url = filings_ex99[0].url
        filings = await SEC_Filing.from_metadatas_async(metadatas)
        logging.info(f"Extracting events for {filings[5].filing_metadata.document_url}")
        chain_of_thought_extractor = ChainOfThoughtExtractor()
        chain_of_thoughts = await chain_of_thought_extractor.extract_chain_of_thoughts(
            filings[5]
        )
        logging.info(f"Chain of thoughts: {chain_of_thoughts}")
        # Convert to filing metadatas
        # bitcoin_filing_metadatas = [
        #     self._get_filing_metadata(hit.accession_number)
        #     for hit in filtered_bitcoin_filing_hits
        #     if self._get_filing_metadata(hit.accession_number) is not None
        # ]
        # logging.info(
        #     f"Retrieved {len(bitcoin_filing_metadatas)} filings for {self.name}"
        # )
        # # Load html content for metadatas
        # filings = await SEC_Filing.from_metadatas_async(bitcoin_filing_metadatas)
        # logging.info(f"First filing: {filings[0]}")
        return self
