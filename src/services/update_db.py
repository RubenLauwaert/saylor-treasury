import logging
from datetime import date, datetime
from data_repositories.public_entity_repo import PublicEntityRepository
from models.sec_edgar.submissions.SubmissionsRequest import SubmissionsRequest
from models.sec_edgar.efts.EFTS_Request import EFTS_Request, EFTS_Response
from models.PublicEntity import PublicEntity
from models.filing.sec_8k.Filing_8K import Filing_8K
from models.filing.sec_424B5.Filing_424B5 import Filing_424B5
from models.filing.sec_10q.Filing_10Q import Filing_10Q
from pymongo.collection import Collection
from queries import base_bitcoin_8k_company_query, base_bitcoin_balance_sheet_query
from database import public_entity_collection
from data_repositories.util_repo import UtilRepository
from util import ImportantDates
from logging import Logger
from services.edgar import get_entity_ciks_from_queries_async
from models.sec_edgar.efts.query import Base_Bitcoin_Query

from services.throttler import ApiThrottler


class DatabaseUpdater:

    # Database repositories
    entity_repo: PublicEntityRepository
    util_repo: UtilRepository
    logger: Logger

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.entity_repo = PublicEntityRepository()
            self.util_repo = UtilRepository()
            self.logger.info("Initialized database repositories.")
        except Exception as e:
            self.logger.error(f"Error initializing database repositories: {e}")

    async def sync_bitcoin_entities(self):

        try:

            entities_w_ticker = self.entity_repo.get_entities_by_type("operating")
            self.logger.info(f"Found {len(entities_w_ticker)} entities with tickers.")
            start_date = max(
                ImportantDates.MSTR_GENESIS_DATE.value,
                self.util_repo.get_last_synced_entities().date(),
            )
            self.logger.info(f"Querying entities from start date : {start_date}")
            # Retrieve all public entities via Edgar API
            search_query_1 = (
                Base_Bitcoin_Query(forms=["8-K"]).set_start_date(start_date).to_dict()
            )
            search_query_2 = (
                Base_Bitcoin_Query(forms=["10-Q"]).set_start_date(start_date).to_dict()
            )
            search_query_3 = (
                Base_Bitcoin_Query(forms=["10-K"]).set_start_date(start_date).to_dict()
            )

            all_entity_ciks = await get_entity_ciks_from_queries_async(
                [search_query_1, search_query_2, search_query_3]
            )
            # Retrieve all entities in the database
            db_entities = self.entity_repo.get_all_entities()
            db_ciks = {entity.cik for entity in db_entities}
            # Find new entities to add to the database
            new_entity_ciks = [cik for cik in all_entity_ciks if cik not in db_ciks]
            self.logger.info(f"Found {len(new_entity_ciks)} new entities to add.")
            if len(new_entity_ciks) > 0:
                new_entities = await PublicEntity.from_ciks(new_entity_ciks)
                self.entity_repo.add_entities(new_entities)
            # Update the last synced entities timestamp
            self.util_repo.update_last_synced_entities(datetime.now())
            self.logger.info(f"Synced {len(new_entity_ciks)} new entities.")

            # After initializing db with the entities , append bitcoin entity tags to the entities
            await self.identify_bitcoin_tags()

        except Exception as e:
            self.logger.error(f"Error syncing bitcoin entities: {e}")

    async def identify_bitcoin_tags(self):

        # Get entities with tickers whose tag has not yet been set
        entities = self.entity_repo.get_entities_w_existing_ticker()
        entities_to_update = [
            entity for entity in entities if entity.are_tags_identified == False
        ]

        # Identify the tags for the entities
        tasks = [
            lambda entity=entity: self.entity_repo.identify_bitcoin_tags_for(entity)
            for entity in entities_to_update
        ]
        await ApiThrottler.throttle_requests(request_funcs=tasks)

    async def sync_bitcoin_filings(self):

        # Only get entities with tickers
        public_entities = self.entity_repo.get_entities_w_existing_ticker()

        # Load the bitcoin filing hits for the entities
        tasks = [
            lambda entity=entity: self.entity_repo.update_bitcoin_filings_for(entity)
            for entity in public_entities
        ]
        public_entities = await ApiThrottler.throttle_requests(request_funcs=tasks)

    async def extract_tenq_xbrl_facts(self):
        # Only get entities with tickers
        public_entities = self.entity_repo.get_entities_w_existing_ticker()

        # TODO : Make more performant by reasoning how many 10Q filings are not yet processed
        # Extract official btc holding statements from 10Q bitcoin filings
        # tasks = [lambda entity=entity: self.entity_repo.update_tenq_xbrl_facts_for(entity) for entity in public_entities]
        # public_entities = await ApiThrottler.throttle_requests(request_funcs=tasks)

        for entity in public_entities:
            await self.entity_repo.update_tenq_xbrl_facts_for(entity)

    async def sync_gen_ai_statements(self):
        # Only get entities with an active treasury program
        public_entities = self.entity_repo.get_active_bitcoin_treasury_entities()

        for entity in public_entities:
            await self.entity_repo.update_gen_ai_statements_for(entity)

    # Reset the gen_ai bitcoin_data for all entities
    def reset_gen_ai_bitcoin_data(self):
        entities = self.entity_repo.get_all_entities()
        for entity in entities:
            entity.reset_bitcoin_data_gen_ai()
            self.entity_repo.add_entity(entity)
        self.logger.info("Reset GenAI bitcoin data for all entities.")
