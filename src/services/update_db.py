import logging
from datetime import date
from data_repositories.public_entity_repo import PublicEntityRepository
from models.sec_edgar.submissions.SubmissionsRequest import SubmissionsRequest
from models.sec_edgar.efts.EFTS_Request import EFTS_Request, EFTS_Response
from models.PublicEntity import PublicEntity
from models.filing.sec_8k.Filing_8K import Filing_8K
from models.filing.sec_424B5.Filing_424B5 import Filing_424B5
from models.filing.sec_10q.Filing_10Q import Filing_10Q
from pymongo.collection import Collection
from queries import base_bitcoin_8k_company_query, base_bitcoin_balance_sheet_query
from database import (
    public_entity_collection
)
from util import ImportantDates
from logging import Logger
from services.edgar import get_entity_ciks_from_queries_async
from models.sec_edgar.efts.query import Base_Bitcoin_Query

from services.throttler import ApiThrottler


class DatabaseUpdater:

    # Database repositories
    entity_repo: PublicEntityRepository
    logger: Logger

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.entity_repo = PublicEntityRepository(public_entity_collection)
            self.logger.info("Initialized database repositories.")
        except Exception as e:
            self.logger.error(f"Error initializing database repositories: {e}")

    async def sync_bitcoin_entities(self):

        try:
            
            entities_w_ticker = self.entity_repo.get_entities_by_type("operating")
            self.logger.info(f"Found {len(entities_w_ticker)} entities with tickers.")
            # Retrieve all public entities via Edgar API
            search_query_1 = Base_Bitcoin_Query(forms=["8-K"]).set_start_date(ImportantDates.MSTR_GENESIS_DATE.value).to_dict()
            search_query_2 = Base_Bitcoin_Query(forms=["10-Q"]).set_start_date(ImportantDates.MSTR_GENESIS_DATE.value).to_dict()
            search_query_3 = Base_Bitcoin_Query(forms=["10-K"]).set_start_date(ImportantDates.MSTR_GENESIS_DATE.value).to_dict()

            all_entity_ciks = await get_entity_ciks_from_queries_async([search_query_1,search_query_2, search_query_3])
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
            
            
    async def sync_bitcoin_filings(self):
        
        # Only get entities with tickers
        public_entities = self.entity_repo.get_entities_w_existing_ticker()
        
        # Load the bitcoin filing hits for the entities
        tasks = [lambda entity=entity: entity.load_new_bitcoin_filings() for entity in public_entities]
        public_entities = await ApiThrottler.throttle_requests(request_funcs=tasks)
        
        # for entity in public_entities:
        #     # Load the bitcoin filing hits
        #     await entity.load_new_bitcoin_filings()
        #     self.logger.info(f"Synced new bitcoin filings for entity: {entity.name}")
        
        

        self.entity_repo.update_entities(public_entities)
        
    async def parse_bitcoin_filings(self):
        # Only get entities with tickers
        public_entities = self.entity_repo.get_entities_w_existing_ticker()
        
        # Extract official btc holding statements from 10Q bitcoin filings
        tasks = [lambda entity=entity: entity.extract_official_btc_holding_statements() for entity in public_entities]
        public_entities = await ApiThrottler.throttle_requests(request_funcs=tasks)
        
        self.entity_repo.update_entities(public_entities)
        

            


