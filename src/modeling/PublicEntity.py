import asyncio
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Optional, List, Set
from modeling.sec_edgar.submissions.SubmissionsResponse import SubmissionsResponse
import logging

from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from modeling.filing.SEC_Filing import SEC_Filing
from modeling.filing.SEC_Form_Types import SEC_Form_Types

from services.ai.bitcoin_events import *
from services.ai.events_transformer import *
from modeling.filing.Bitcoin_Filing import Bitcoin_Filing
from util import ImportantDates
from collections import defaultdict



class BitcoinTreasuryUpdateStatement(BaseModel):
    # Data about the bitcoin treasury update
    bitcoin_treasury_update: BitcoinTreasuryUpdate
    
    # Data about the filing where the statement was found
    filing_url: str
    file_date: str
    accession_number: str
    form_type: str
    file_type: str
    
    @classmethod
    def from_bitcoin_filing(cls, filing: Bitcoin_Filing) -> "BitcoinTreasuryUpdateStatement":
        return cls(bitcoin_treasury_update=filing.bitcoin_treasury_update,
                   filing_url=filing.url,
                   file_date=filing.file_date,
                   accession_number=filing.accession_number,
                   form_type=filing.form_type,
                   file_type=filing.file_type)


class BitcoinHoldingsStatement(BaseModel):
    
    # Data about the bitcoin holdings
    bitcoin_data: TotalBitcoinHoldings
    
    # Data about the filing where the statement was found
    filing_url: str
    file_date: str
    accession_number: str
    form_type: str
    file_type: str
    
    @classmethod
    def from_bitcoin_filing(cls, filing: Bitcoin_Filing) -> "BitcoinHoldingsStatement":
        return cls(bitcoin_data=filing.total_bitcoin_holdings,
                   filing_url=filing.url,
                   file_date=filing.file_date,
                   accession_number=filing.accession_number,
                   form_type=filing.form_type,
                   file_type=filing.file_type)
    
    


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
    exchanges: Optional[List[Any]] = Field(
        default=None, description="The stock exchanges the company is listed on."
    )
    category: Optional[str] = Field(
        default=None, description="The category of the company."
    )
    phone: Optional[str] = Field(default=None, description="The company's phone number.")
    
    # Filing data
    
    filing_metadatas: List[SEC_Filing_Metadata] = Field(
        default=[], description="The list of submissions for this entity."
    )

    accepted_bitcoin_filing_types: List[SEC_Form_Types] = Field(
        default=[
            SEC_Form_Types.FORM_8K,
            SEC_Form_Types.FORM_10Q,
            SEC_Form_Types.FORM_10K,
            SEC_Form_Types.FORM_424B5

        ],
        description="The list of accepted filing types for bitcoin filings.",
    )
    bitcoin_filings: List[Bitcoin_Filing] = Field(
        default=[],
        description="The list of Bitcoin filings, containing the word bitcoin for this entity,",
    )
    
    # Bitcoin treasury data
    total_btc_holdings: float = Field(
        default=0.0,
        description="The total amount of Bitcoin held by the entity.",
    )
    
    btc_treasury_update_statements: List[BitcoinTreasuryUpdateStatement] = Field(default=[], description="The list of Bitcoin treasury updates for the entity.")
    
    btc_treasury_holdings_statements: List[BitcoinHoldingsStatement] = Field(default=[], description="The list of Bitcoin treasury holdings statements for the entity.")
    

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
        exchanges = submission_response.get("exchanges") or []
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
        
        # # Load the html content for the new bitcoin filings
        # new_bitcoin_filings_w_content = await Bitcoin_Filing.load_html_content_for(new_bitcoin_filings)
        
        # # Extract the bitcoin events for the new bitcoin filings (adhere to rate limit)
        # new_bitcoin_filings_w_events = await Bitcoin_Filing.extract_bitcoin_events_for(new_bitcoin_filings_w_content)
        
        # # Parse the extracted events into Bitcoin treasury statuses
        # new_bitcoin_filings_w_treasury_stats = await Bitcoin_Filing.parse_bitcoin_events_for(new_bitcoin_filings_w_events)
        
        # # Remove the raw text from the bitcoin filing to save space in the database
        # for filing in new_bitcoin_filings_w_treasury_stats:
        #     filing.raw_text = ""
        
        # Add the new bitcoin filings to the entity
        self.bitcoin_filings.extend(all_bitcoin_filings)
 
        return self
    
    
    
    def get_btc_amt_in_treasury(self) -> float:
        # Return the latest and most accurate bitcoin holdings
        for filing in sorted(self.bitcoin_filings, key=lambda x: datetime.fromisoformat(x.file_date), reverse=True):
            if filing.has_total_bitcoin_holdings:
                return filing.total_bitcoin_holdings.total_bitcoin_holdings
        return 0.0
    
    
    def filter_btc_holdings_statements(self, holding_statements: List[BitcoinHoldingsStatement]) -> List[BitcoinHoldingsStatement]:
        
        filtered_statements = []
        
        # Group holding statements by accession number
        grouped_statements_by_accn = defaultdict(list)
        for statement in holding_statements:
            grouped_statements_by_accn[statement.accession_number].append(statement)
        
        # Group holding statements by btc holdings
        grouped_statements_by_holdings = defaultdict(list)
        for statement in holding_statements:
            grouped_statements_by_holdings[int(statement.bitcoin_data.total_bitcoin_holdings)].append(statement)
        
        for statements in grouped_statements_by_holdings.values():
            if len(statements) == 1:
                filtered_statements.extend(statements)
            elif len(statements) > 1:
                # Get the earliest statement available
                earliest_statement = sorted(statements, key=lambda x: datetime.fromisoformat(x.file_date))[0]
                filtered_statements.append(earliest_statement)
                
        return filtered_statements
    
    def filter_btc_treasury_updates(self, treasury_updates: List[BitcoinTreasuryUpdateStatement], holding_statements: List[BitcoinHoldingsStatement]) -> List[BitcoinTreasuryUpdateStatement]:  
        
        filtered_update_statements = []
        # Sort the filtered_holdings by date
        sorted_holdings = sorted(holding_statements, key=lambda x: datetime.fromisoformat(x.file_date))
        sorted_holdings_wo_first = sorted_holdings[0:]
        # Group treasury updates by bitcoin_amount
        grouped_statements_by_btc_amount = defaultdict(list)
        for statement in treasury_updates:
            grouped_statements_by_btc_amount[int(statement.bitcoin_treasury_update.bitcoin_amount)].append(statement)
        
        # Filter out updates where the bitcoin amount is the same as a reported holding statement (except first one)
        for statements in grouped_statements_by_btc_amount.values():
            earliest_statement : BitcoinTreasuryUpdateStatement = sorted(statements, key=lambda x: datetime.fromisoformat(x.file_date))[0]
            update_amount = int(earliest_statement.bitcoin_treasury_update.bitcoin_amount)
            if(update_amount not in [int(h.bitcoin_data.total_bitcoin_holdings) for h in sorted_holdings_wo_first]):
                filtered_update_statements.append(earliest_statement)
            
                
        return filtered_update_statements
    
    def update_btc_treasury_data(self) -> "PublicEntity":
        
        # Filtered bitcoin treasury holdings statements
        raw_btc_treasury_holdings_statements = [
            BitcoinHoldingsStatement.from_bitcoin_filing(filing) for filing in self.bitcoin_filings if filing.has_total_bitcoin_holdings
        ]
        filtered_btc_treasury_holdings_statements = self.filter_btc_holdings_statements(raw_btc_treasury_holdings_statements)
        self.btc_treasury_holdings_statements = filtered_btc_treasury_holdings_statements
        
        # Filtered bitcoin treasury updates
        raw_btc_treasury_update_statements = [
            BitcoinTreasuryUpdateStatement.from_bitcoin_filing(filing) for filing in self.bitcoin_filings if filing.has_bitcoin_treasury_update
        ]
        
        filtered_btc_treasury_update_statements = self.filter_btc_treasury_updates(raw_btc_treasury_update_statements, filtered_btc_treasury_holdings_statements)
        self.btc_treasury_update_statements = filtered_btc_treasury_update_statements
        
        # Update the bitcoin holdings for the entity
        self.total_btc_holdings = self.get_btc_amt_in_treasury()
        return self
    
    
    async def load_13fhr_filings(self) -> "PublicEntity":
        
        from modeling.sec_edgar.efts.query import Base_EFTS_Query
        from services.edgar import get_query_result_async
        from modeling.parsers.sec_13f_hr.parser_13fhr_xml import parse_sec_xml
        import pandas as pd
        
        # Logger
        logger = logging.getLogger(self.__class__.__name__)
              

        # Retrieve QueryResult (QueryHits) for 13FHR query
        base_13FHR_query = Base_EFTS_Query(q="MICROSTRATEGY", forms=["13F-HR"], ciks="0000093751",startdt=date(2024,1,1).isoformat()).to_dict()
        query_result = await get_query_result_async(q=base_13FHR_query)
        hits = query_result.hits
        ciks = set([hit.cik for hit in hits])
        logger.info(len(ciks))
        urls = [hit.url for hit in hits]
        dates = [hit.file_date for hit in hits]
        logger.info(dates)
        filings_raw = await SEC_Filing.get_html_content_for(urls)
        parsed_content = [parse_sec_xml(filing_raw) for filing_raw in filings_raw]
        filtered_parsed_content = [entry for entry in parsed_content[2] if "MICROSTRATEGY" in entry["nameOfIssuer"]]
        # Convert to DataFrame
        df = pd.DataFrame(filtered_parsed_content)
    
        logger.info(df)
       
        return self