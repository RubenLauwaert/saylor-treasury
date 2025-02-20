import logging
from datetime import date
from data_repositories.public_entity_repo import PublicEntityRepository
from data_repositories.sec_filing_metadata_repo import SEC_Filing_Metadata_Repository
from data_repositories.sec_filing_8k_repo import SEC_Filing_8K_Repository
from modeling.sec_edgar.submissions.SubmissionsRequest import SubmissionsRequest
from modeling.sec_edgar.efts.EFTS_Request import EFTS_Request, EFTS_Response
from modeling.PublicEntity import PublicEntity
from modeling.filing.sec_8k.Filing_8K import Filing_8K
from modeling.filing.sec_424B5.Filing_424B5 import Filing_424B5
from modeling.filing.sec_10q.Filing_10Q import Filing_10Q
from pymongo.collection import Collection
from queries import base_bitcoin_8k_company_query, base_bitcoin_balance_sheet_query
from database import (
    public_entity_collection,
    sec_filing_metadatas_collection,
    filings_8k_collection,
)
from util import ImportantDates
from logging import Logger
from services.edgar import get_entity_ciks_from_queries_async
from modeling.sec_edgar.efts.query import Base_Bitcoin_Query


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

    async def sync_bitcoin_entities(self):

        try:
            
            # Bitcoin mining entities
            mining_entities = self.entity_repo.get_bitcoin_mining_entities()
            etfs = self.entity_repo.get_foreign_entities()
            self.logger.info([entity.ticker for entity in mining_entities])
            self.logger.info([entity.ticker for entity in etfs])
            # Retrieve all public entities via Edgar API
            search_query = Base_Bitcoin_Query().set_start_date(ImportantDates.TODAY.value).to_dict()
            all_entity_ciks = await get_entity_ciks_from_queries_async([search_query])
            # Retrieve all entities in the database
            db_entities = self.entity_repo.get_all_entities()
            db_ciks = {entity.cik for entity in db_entities}
            # Find new entities to add to the database
            new_entity_ciks = [
                cik for cik in all_entity_ciks if cik not in db_ciks
            ]
            self.logger.info(f"Found {len(new_entity_ciks)} new entities to add.")
            if len(new_entity_ciks) > 0:
                new_entities = await PublicEntity.from_ciks(new_entity_ciks)
                self.entity_repo.add_entities(new_entities)
            self.logger.info(f"Synced {len(new_entity_ciks)} new entities.")
        except Exception as e:
            self.logger.error(f"Error syncing bitcoin entities: {e}")
            


