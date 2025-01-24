import logging
from datetime import date
from data_repositories.public_entity_repo import PublicEntityRepository
from data_repositories.sec_filing_metadata_repo import SEC_Filing_Metadata_Repository
from data_repositories.sec_filing_8k_repo import SEC_Filing_8K_Repository
from modeling.sec_edgar.submissions.SubmissionsRequest import SubmissionsRequest
from modeling.sec_edgar.efts.EFTS_Request import EFTS_Request, EFTS_Response
from modeling.PublicEntity import PublicEntity
from modeling.filing.sec_8k.Filing_8K import Filing_8K
from services.ai.Filing_Summarizer_8K import Filing_Summarizer_8K
from pymongo.collection import Collection
from queries import base_bitcoin_8k_company_query, base_bitcoin_balance_sheet_query
from database import (
    public_entity_collection,
    sec_filing_metadatas_collection,
    filings_8k_collection,
)
from services.ai.BTC_Updates_Extractor import Bitcoin_Updates_Extractor
from util import ImportantDates
from logging import Logger


class DatabaseUpdater:

    # Database repositories
    entity_repo: PublicEntityRepository
    metadata_repo: SEC_Filing_Metadata_Repository
    filing_8k_repo: SEC_Filing_8K_Repository
    logger: Logger

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.entity_repo = PublicEntityRepository(public_entity_collection)
            self.metadata_repo = SEC_Filing_Metadata_Repository(
                sec_filing_metadatas_collection
            )
            self.filing_8k_repo = SEC_Filing_8K_Repository(filings_8k_collection)
            self.logger.info("Initialized database repositories.")
        except Exception as e:
            self.logger.error(f"Error initializing database repositories: {e}")

    def sync_bitcoin_entities(self):
        existing_entities = self.entity_repo.get_all_entities()
        existing_ciks = {entity.cik for entity in existing_entities}
        try:
            efts_response = EFTS_Request(query=base_bitcoin_8k_company_query)
            if efts_response is not None:
                all_entities = efts_response.get_entities()
                new_entities = [
                    entity for entity in all_entities if entity.cik not in existing_ciks
                ]
                new_entity_tickers = {new_entity.ticker for new_entity in new_entities}
                if len(new_entities) > 0:
                    self.entity_repo.add_entities(new_entities)
                    self.logger.info(
                        f"Added new entities to db with tickers: {new_entity_tickers}"
                    )
                else:
                    logging.info(f"No new entities to add to db !")
        except Exception as e:
            self.logger.error(f"Error adding new entities to database: {e}")

    def sync_filing_metadatas_for(self, public_entity: PublicEntity):
        latest_filing_date = self.metadata_repo.get_latest_filing_metadata_date_for(
            public_entity
        )
        try:
            submission_resp = SubmissionsRequest.from_cik(
                public_entity.cik
            ).resp_content
            filing_metadatas = submission_resp.filing_metadatas
            new_filing_metadatas = [
                filing_metadata
                for filing_metadata in filing_metadatas
                if date.fromisoformat(filing_metadata.filing_date) > latest_filing_date
            ]
            self.logger.info(
                f"Retrieved {len(new_filing_metadatas)} new filing metadatas for {public_entity.ticker}."
            )
            self.metadata_repo.add_filing_metadatas(new_filing_metadatas)
            logging.info(f"Synced filing metadatas for {public_entity.ticker}.")
        except Exception as e:
            self.logger.error(
                f"Error updating filing metadatas for {public_entity.ticker}: {e}"
            )

    async def sync_filings_8k_for(
        self, ticker: str, after_date: date = ImportantDates.MSTR_GENESIS_DATE.value
    ):

        try:
            public_entity = self.entity_repo.get_entity_by_ticker(ticker)
            # First sync the filing_metadatas for the entity
            self.sync_filing_metadatas_for(public_entity)
            # Retrieve all 8-k filing metadatas for the entity
            filing_8k_metadatas = (
                self.metadata_repo.get_8k_filing_metadatas_for_after_date(
                    public_entity, after_date
                )
            )
            # Retrieve existing 8-k filings for the entity
            existing_filings_8k = self.filing_8k_repo.get_filings_for_entity_after_date(
                public_entity, after_date
            )
            # Check if there are new filings to parse and sync
            new_filing_8k_metadatas = [
                filing_metadata
                for filing_metadata in filing_8k_metadatas
                if filing_metadata.accession_number
                not in [
                    filing.filing_metadata.accession_number
                    for filing in existing_filings_8k
                ]
            ]
            # Create parsed 8k-filings
            new_filings_8k = await Filing_8K.from_metadatas_async(
                new_filing_8k_metadatas
            )
            # Sync new filings to db
            self.filing_8k_repo.add_filings(new_filings_8k)
            self.logger.info(
                f"Synced {len(new_filings_8k)} new 8-K filings for {public_entity.ticker}."
            )
        except Exception as e:
            self.logger.error(
                f"Error updating 8-K filings for {public_entity.ticker}: {e}"
            )

    async def summarize_filings_8k_for(
        self, ticker: str, after_date=ImportantDates.MSTR_GENESIS_DATE.value
    ):

        try:
            # Retrieve all 8-k filings for the entity that are not yet summarized
            public_entity = self.entity_repo.get_entity_by_ticker(ticker)
            all_filings_8k = self.filing_8k_repo.get_filings_for_entity_after_date(
                public_entity, after_date
            )
            not_yet_summarized = [
                filing for filing in all_filings_8k if filing.is_summarized is False
            ]
            # Summarize the filings
            summarizer = Filing_Summarizer_8K()
            summarized_filings = await summarizer.summarize_filings_optimized(
                not_yet_summarized
            )
            # Update the filings in the db
            self.filing_8k_repo.update_filings(summarized_filings)
        except Exception as e:
            self.logger.error(f"Error summarizing 8-K filings for {ticker}: {e}")

    async def update_bitcoin_purchases(
        self, ticker: str, after_date=ImportantDates.MSTR_GENESIS_DATE.value
    ):
        try:
            # Retrieve all 8-k filings for the entity that are not yet summarized
            public_entity = self.entity_repo.get_entity_by_ticker(ticker)
            all_filings_8k = self.filing_8k_repo.get_filings_for_entity_after_date(
                public_entity, after_date
            )
            # Extract bitcoin purchases from the filings
            bitcoin_extractor = Bitcoin_Updates_Extractor()
            bitcoin_purchases = await bitcoin_extractor.extract_bitcoin_purchases(
                all_filings_8k
            )
            filtered_bitcoin_purchases = [
                bp for bp in bitcoin_purchases if bp is not None
            ]
            purchase_dates = [
                purchase.purchase_date.to_date()
                for purchase in filtered_bitcoin_purchases
            ]
            bitcoin_purchase_amounts = [
                purchase.btc_purchase_amount for purchase in filtered_bitcoin_purchases
            ]
            sum_amounts = sum(bitcoin_purchase_amounts)
            self.logger.info(f"Purchase dates: {purchase_dates}")
            self.logger.info(f"Purchase amounts: {bitcoin_purchase_amounts}")
            self.logger.info(f"Total BTC purchased: {sum_amounts}")
            self.logger.info(
                f"Extracted {len(filtered_bitcoin_purchases)} bitcoin purchases for {ticker}."
            )
            # Update the database with the bitcoin purchases
        except Exception as e:
            self.logger.error(f"Error updating bitcoin purchases for {ticker}: {e}")
