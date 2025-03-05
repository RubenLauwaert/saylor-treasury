import asyncio
from datetime import datetime, date
import pandas as pd
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Optional, List, Set
from models.sec_edgar.submissions.SubmissionsResponse import SubmissionsResponse
import logging

from models.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from models.filing.SEC_Filing import SEC_Filing
from models.filing.SEC_Form_Types import SEC_Form_Types

from services.ai.bitcoin_events import *
from models.filing.Bitcoin_Filing import Bitcoin_Filing
from models.util import *
from collections import defaultdict

from models.BitcoinData import BitcoinData
from models.sec_edgar.efts.query import Base_Bitcoin_Query
from services.edgar import (
    get_query_result_async,
    get_query_results_async,
    get_raw_content_text_for,
)
from util import ImportantDates


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
    phone: Optional[str] = Field(
        default=None, description="The company's phone number."
    )

    # Filing data

    filing_metadatas: List[SEC_Filing_Metadata] = Field(
        default=[], description="The list of submissions for this entity."
    )

    accepted_bitcoin_filing_types: List[SEC_Form_Types] = Field(
        default=[
            SEC_Form_Types.FORM_8K,
            SEC_Form_Types.FORM_10Q,
            SEC_Form_Types.FORM_10K,
            SEC_Form_Types.FORM_424B5,
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

    # Bitcoin entity tag

    # Tag of the bitcoin enitity
    bitcoin_entity_tags: List[BitcoinEntityTag] = Field(
        default=[BitcoinEntityTag.MENTIONED_BTC_IN_FILING],
        description="The tag of the bitcoin entity.",
    )
    are_tags_identified: bool = Field(
        default=False, description="Whether the bitcoin entity tag has been identified."
    )

    # Bitcoin data

    bitcoin_data: BitcoinData = Field(
        default=BitcoinData(), description="The data about the Bitcoin entity."
    )

    # Last updated timestamps
    last_updated_bitcoin_filings: datetime = Field(
        default=datetime.min,
        description="The timestamp of the last update of the Bitcoin filings. (SEC filings with the word 'bitcoin')",
    )
    last_updated_submissions: datetime = Field(
        default=datetime.min,
        description="The timestamp of the last update of the submissions for this entity.",
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
        exchanges = submission_response.get("exchanges") or []
        category = submission_response.get("category")
        phone = submission_response.get("phone")

        # Extract recent filings
        filing_metadatas = SubmissionsResponse.from_dict(
            submission_response
        ).filing_metadatas

        last_updated_submissions = datetime.now()

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
            last_updated_submissions=last_updated_submissions,
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

    def get_ai_generated_holding_statements(
        self,
    ) -> List[BitcoinHoldingsDisclosure_GEN_AI]:
        return self.bitcoin_data.get_high_confidence_holding_disclosures()

    # Filing metadatas

    def get_filing_metadatas(self) -> List[SEC_Filing_Metadata]:
        return self.filing_metadatas

    def get_filing_metadatas_by_form_type(
        self, form_type: str
    ) -> List[SEC_Filing_Metadata]:
        return [filing for filing in self.filing_metadatas if filing.form == form_type]

    def _get_filing_metadata(
        self, accession_number: str
    ) -> Optional[SEC_Filing_Metadata]:
        for filing_metadata in self.filing_metadatas:
            if filing_metadata.accession_number == accession_number:
                return filing_metadata
        return None

    # Bitcoin filings

    def get_bitcoin_filings(self) -> List[Bitcoin_Filing]:
        return self.bitcoin_filings

    def get_bitcoin_filings_by_file_type(self, file_type: str) -> List[Bitcoin_Filing]:
        return [
            filing for filing in self.bitcoin_filings if filing.file_type == file_type
        ]

    def get_bitcoin_filings_by_form_type(self, form_type: str) -> List[Bitcoin_Filing]:
        return [
            filing for filing in self.bitcoin_filings if filing.form_type == form_type
        ]

    # Setters

    def append_bitcoin_entity_tag(self, tag: BitcoinEntityTag):
        if tag not in self.bitcoin_entity_tags:
            self.bitcoin_entity_tags.append(tag)
        if self.are_tags_identified == False:
            self.are_tags_identified = True

    def reset_bitcoin_filings(self):
        self.bitcoin_filings = []
        self.last_updated_bitcoin_filings = datetime.min

    def reset_bitcoin_filings_all_states(self):
        bitcoin_filings_reset = [
            filing.reset_all_states() for filing in self.bitcoin_filings
        ]
        self.bitcoin_filings = bitcoin_filings_reset

    def reset_bitcoin_filings_gen_ai_states(self):
        self.bitcoin_filings = [
            filing.reset_gen_ai_states() for filing in self.bitcoin_filings
        ]

    def reset_bitcoin_data(self):
        self.bitcoin_data = BitcoinData()
        self.reset_bitcoin_filings_all_states()

    def reset_bitcoin_data_gen_ai(self):
        self.bitcoin_data.general_bitcoin_statements_gen_ai = []
        self.bitcoin_data.holding_statements_gen_ai = []

    # Updaters

    # Updates the list of Bitcoin filings for the entity
    async def update_bitcoin_filings(self) -> "PublicEntity":

        from models.sec_edgar.efts.query import Base_Bitcoin_Query
        from services.edgar import get_query_result_async

        # Logger
        logger = logging.getLogger(self.__class__.__name__)

        start_date = max(
            ImportantDates.BTC_GENESIS_DATE.value,
            self.last_updated_bitcoin_filings.date(),
        )

        # Retrieve QueryResult (QueryHits) for bitcoin query (keyword "bitcoin")
        base_bitcoin_query = Base_Bitcoin_Query(
            ciks=self.cik, startdt=start_date.isoformat()
        ).model_dump(exclude_none=True)
        query_result = await get_query_result_async(q=base_bitcoin_query)
        bitcoin_filing_hits = query_result.hits
        # Only store hits with accepted form types
        filtered_bitcoin_filing_hits = [
            hit
            for hit in bitcoin_filing_hits
            if hit.form_type in self.accepted_bitcoin_filing_types
        ]

        # Convert QueryHits to Bitcoin_Filings
        all_bitcoin_filings = [
            Bitcoin_Filing.from_query_hit(hit) for hit in filtered_bitcoin_filing_hits
        ]

        # Filter out filings that are already stored
        new_bitcoin_filings = [
            filing
            for filing in all_bitcoin_filings
            if filing.url not in [bf.url for bf in self.bitcoin_filings]
        ]

        # Add the new bitcoin filings to the entity
        self.bitcoin_filings.extend(new_bitcoin_filings)
        self.last_updated_bitcoin_filings = datetime.now()

        return self

    # Updates the bitcoin data for the entity

    async def extract_official_bitcoin_data_tenqs_xbrl(self) -> "PublicEntity":
        from models.parsers.sec_10q.XBRL_Parser_10Q import Parser10QXBRL
        from services.throttler import ApiThrottler

        # Logger
        logger = logging.getLogger(self.__class__.__name__)
        # Get official bitcoin holding statements for public entity
        entity_tenqs = self.get_bitcoin_filings_by_file_type(file_type="10-Q")
        unparsed_tenqs = [tenq for tenq in entity_tenqs if not tenq.did_parse_xbrl]
        logger.info(
            f"Found {len(unparsed_tenqs)} 10-Q filings to extract XBRL facts for {self.ticker}"
        )
        # urls necessary for retrieving xbrl content
        xbrl_urls = [tenq.url.replace(".htm", "_htm.xml") for tenq in unparsed_tenqs]
        raw_xbrl_contents = await get_raw_content_text_for(xbrl_urls)
        raw_xbrl_contents = [
            content for content in raw_xbrl_contents if content[1] != ""
        ]
        # parsed xbrl contents
        parsed_xbrl_contents = [
            Parser10QXBRL(
                xbrl_url=xbrl_content[0],
                xbrl_string=xbrl_content[1],
                ticker=self.ticker,
            )
            for xbrl_content in raw_xbrl_contents
        ]
        # Extract bitcoin holdings from parsed xbrl content
        tasks_holding_statements = [
            lambda parsed_content=parsed_content: parsed_content.extract_bitcoin_holdings()
            for parsed_content in parsed_xbrl_contents
        ]
        holding_results = await ApiThrottler.throttle_openai_requests(
            request_funcs=tasks_holding_statements
        )

        # Remove duplicates from holding statements
        for xbrl_url, holding_statements in holding_results:
            original_url = xbrl_url.replace("_htm.xml", ".htm")
            filing = [
                filing for filing in unparsed_tenqs if filing.url == original_url
            ][0]
            filing.did_parse_xbrl = True
            for statement in holding_statements:
                self.bitcoin_data.append_holding_statement_xbrl(
                    HoldingStatementTenQ(statement=statement, filing=filing)
                )

        # TODO Extract Fair Value Statements for public entity

        tasks_fair_value_statements = [
            lambda parsed_content=parsed_content: parsed_content.extract_bitcoin_fair_value()
            for parsed_content in parsed_xbrl_contents
        ]
        fair_value_results = await ApiThrottler.throttle_openai_requests(
            request_funcs=tasks_fair_value_statements
        )

        # Remove duplicates from fair value statements
        for xbrl_url, fair_value_statements in fair_value_results:
            original_url = xbrl_url.replace("_htm.xml", ".htm")
            filing = [
                filing for filing in unparsed_tenqs if filing.url == original_url
            ][0]
            for statement in fair_value_statements:
                self.bitcoin_data.append_fair_value_statement_xbrl(
                    FairValueStatementTenQ(statement=statement, filing=filing)
                )
            print(
                [
                    statement.statement
                    for statement in self.bitcoin_data.fair_value_statements_xbrl
                ]
            )
        return self

    async def extract_general_statements_genai_eightks(self) -> "PublicEntity":
        from services.throttler import ApiThrottler
        from models.parsers.generic.Filing_Parser_Generic import Filing_Parser_Generic
        from services.ai.bitcoin_statements import BitcoinStatementsExtractor

        # Retrieve 8-K Bitcoin filings where events are not already extracted (this includes EX-99.1 filings)
        eightks = [
            filing
            for filing in self.get_bitcoin_filings_by_form_type("8-K")
            if (filing.file_type == "8-K" or filing.file_type == "EX-99.1")
            and date.fromisoformat(filing.file_date) > date(2024, 1, 1)
        ]

        eightks_already_extracted = self.bitcoin_data.get_eightks_parsed_general()
        eightks_to_extract = [
            filing
            for filing in eightks
            if filing.url not in [filing.url for filing in eightks_already_extracted]
        ]

        if len(eightks_to_extract) > 0:
            # Retrieve content of those 8-K filings
            raw_contents = await get_raw_content_text_for(
                [filing.url for filing in eightks_to_extract]
            )
            cleaned_contents = [
                Filing_Parser_Generic.get_cleaned_text(content[1])
                for content in raw_contents
            ]
            # Async GenAI tasks
            extractor = BitcoinStatementsExtractor()
            gen_ai_tasks = [
                lambda cleaned_content=cleaned_content: extractor.extract_statements(
                    raw_text=cleaned_content
                )
                for cleaned_content in cleaned_contents
            ]
            gen_ai_results: List[StatementResults] = (
                await ApiThrottler.throttle_openai_requests(request_funcs=gen_ai_tasks)
            )

            for filing, statement_result in zip(eightks_to_extract, gen_ai_results):
                gen_ai_statement_result = StatementResult_GEN_AI(
                    filing=filing, statements=statement_result.statements
                )
                self.bitcoin_data.append_bitcoin_statement_gen_ai(
                    gen_ai_statement_result
                )

        return self

    async def extract_bitcoin_holdings_gen_ai_eightks(self) -> "PublicEntity":
        from services.throttler import ApiThrottler
        from services.ai.bitcoin_statements import BitcoinStatementsExtractor

        # Retrieve all eight-k filings where general statements are extracted  and holdings are not
        eightks_parsed_general = self.bitcoin_data.get_eightks_parsed_general()
        eightks_parsed_holdings = (
            self.bitcoin_data.get_eightks_parsed_holding_statements()
        )
        not_yet_extracted_holdings = [
            filing
            for filing in eightks_parsed_general
            if filing.url
            not in [
                eightks_parsed_holdings.url
                for eightks_parsed_holdings in eightks_parsed_holdings
            ]
        ]
        print(len(not_yet_extracted_holdings))
        if len(not_yet_extracted_holdings) > 0:
            # Extract holding statements
            general_statements = [
                statement
                for statement in self.bitcoin_data.general_bitcoin_statements_gen_ai
                if statement.filing.url
                in [filing.url for filing in not_yet_extracted_holdings]
            ]
            extractor = BitcoinStatementsExtractor()
            tasks = [
                lambda statement=statement: extractor.extract_holding_statements(
                    statement.statements
                )
                for statement in general_statements
            ]
            gen_ai_holding_results: List[HoldingStatementsResult] = (
                await ApiThrottler.throttle_openai_requests(request_funcs=tasks)
            )
            filing_holding_statements = list(
                zip(not_yet_extracted_holdings, gen_ai_holding_results)
            )

            for filing, holding_statements_result in filing_holding_statements:
                self.bitcoin_data.append_holding_statement_gen_ai(
                    HoldingStatementResult_GEN_AI(
                        statements=holding_statements_result.holding_statements,
                        filing=filing,
                    )
                )
        return self

    # FILE: src/models/PublicEntity.py

    # Update the extract_treasury_updates_gen_ai method:

    async def extract_treasury_updates_gen_ai(self) -> "PublicEntity":
        from services.throttler import ApiThrottler
        from services.ai.bitcoin_statements import BitcoinStatementsExtractor

        # Retrieve all eight-k filings where general statements are extracted and holdings are not
        eightks_parsed_general = self.bitcoin_data.get_eightks_parsed_general()
        eightks_parsed_treasury_updates = (
            self.bitcoin_data.get_eightks_parsed_treasury_update_statements()
        )
        filings_not_yet_extracted = [
            filing
            for filing in eightks_parsed_general
            if filing.url
            not in [
                eightks_parsed_treasury_update.url
                for eightks_parsed_treasury_update in eightks_parsed_treasury_updates
            ]
        ]
        print(len(filings_not_yet_extracted))
        if len(filings_not_yet_extracted) > 0:
            # Extract Treasury updates
            general_statements = [
                statement
                for statement in self.bitcoin_data.general_bitcoin_statements_gen_ai
                if statement.filing.url
                in [filing.url for filing in filings_not_yet_extracted]
            ]
            extractor = BitcoinStatementsExtractor()
            tasks = [
                lambda statement=statement: extractor.extract_treasury_updates(
                    statement.statements
                )
                for statement in general_statements
            ]
            gen_ai_treasury_update_results = (
                await ApiThrottler.throttle_openai_requests(request_funcs=tasks)
            )
            filing_treasury_updates = list(
                zip(filings_not_yet_extracted, gen_ai_treasury_update_results)
            )

            for filing, treasury_update_result in filing_treasury_updates:
                if treasury_update_result:  # Check if result is not None
                    # Extract the treasury_update_statements from the result
                    statements = treasury_update_result.treasury_update_statements

                    # Now create the TreasuryUpdateStatementResult_GEN_AI
                    self.bitcoin_data.append_treasury_update_gen_ai(
                        TreasuryUpdateStatementResult_GEN_AI(
                            statements=statements,
                            filing=filing,
                        )
                    )
            print(filing_treasury_updates)
        return self

    async def extract_gen_ai_bitcoin_data(self) -> "PublicEntity":

        # TODO : Extract Bitcoin events from 8-K Bitcoin filings

        # TODO : Extract Bitcoin Holding Statements from 8-K Bitcoin filings

        return self

    #
    #
    #
    #

    async def identify_bitcoin_tags(self) -> "PublicEntity":

        # Identify miners and crypto service providers
        if self.sic == "6199" and self.ticker != "MSTR":
            bitcoin_mining_query = Base_Bitcoin_Query(
                ciks=self.cik, q="bitcoin NEAR(2) mined"
            ).model_dump(exclude_none=True)
            query_result = await get_query_result_async(q=bitcoin_mining_query)
            if len(query_result.hits) > 0:
                self.append_bitcoin_entity_tag(BitcoinEntityTag.MINER)
            else:
                self.append_bitcoin_entity_tag(BitcoinEntityTag.CRYPTO_SERVICE_PROVIDER)
        # Security brokers, dealers, and exchanges
        if self.sic == "6211":
            self.append_bitcoin_entity_tag(BitcoinEntityTag.CRYPTO_SERVICE_PROVIDER)
        # Identify bitcoin funds / spot bitcoin etfs
        if self.sic == "6221":
            # Spot bitcoin etfs
            if self.ticker in SpotBitcoinETFs:
                self.append_bitcoin_entity_tag(BitcoinEntityTag.SPOT_BITCOIN_ETF)
            # Grayscale trusts
            elif self.ticker in GrayscaleTrusts:
                self.append_bitcoin_entity_tag(BitcoinEntityTag.GRAYSCALE_TRUST)
            # Crypto funds
            else:
                self.append_bitcoin_entity_tag(BitcoinEntityTag.CRYPTO_FUND)

        # Identify active and announced bitcoin treasury strategies
        if self.entity_type == "operating" and not self.sic == "6221":
            active_btc_strategy_query_1 = Base_Bitcoin_Query(
                ciks=self.cik,
                q='acquired NEAR(2) bitcoin -"bitcoin mining" -"bitcoin miners"',
            ).model_dump(exclude_none=True)
            active_btc_strategy_query_2 = Base_Bitcoin_Query(
                ciks=self.cik,
                q='acquisition NEAR(2) bitcoin -"bitcoin mining" -"bitcoin miners"',
            ).model_dump(exclude_none=True)
            active_btc_strategy_query_3 = Base_Bitcoin_Query(
                ciks=self.cik,
                q='purchased NEAR(2) bitcoin -"bitcoin mining" -"bitcoin miners"',
            ).model_dump(exclude_none=True)
            active_btc_strategy_query_4 = Base_Bitcoin_Query(
                ciks=self.cik,
                q='purchase NEAR(2) bitcoin -"bitcoin mining" -"bitcoin miners"',
            ).model_dump(exclude_none=True)
            query_results = await get_query_results_async(
                queries=[
                    active_btc_strategy_query_1,
                    active_btc_strategy_query_2,
                    active_btc_strategy_query_3,
                    active_btc_strategy_query_4,
                ]
            )
            if any(
                [len(query_result.hits) > 0 for query_result in query_results.results]
            ):
                self.append_bitcoin_entity_tag(BitcoinEntityTag.ACTIVE_BTC_STRATEGY)

        self.are_tags_identified = True
        return self
