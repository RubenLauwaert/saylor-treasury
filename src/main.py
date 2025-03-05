from services.daemon import setup_logging
from services.update_db import DatabaseUpdater

from database import public_entity_collection

from data_repositories.public_entity_repo import PublicEntityRepository
from config import sec_edgar_settings as ses
import asyncio

from datetime import date


setup_logging()


# DatabaseUpdater
dbu = DatabaseUpdater()

# Public entity repo
entity_repo = PublicEntityRepository()


async def main():
    # awai  t dbu.sync_bitcoin_entities()

    # await dbu.extract_tenq_xbrl_facts()
    # await dbu.sync_bitcoin_entities()
    # await dbu.sync_bitcoin_filings()
    # await dbu.extract_tenq_xbrl_facts()

    # Get entity
    # dbu.reset_gen_ai_bitcoin_data()
    await dbu.sync_gen_ai_statements()
    # print(entity.get_ai_generated_holding_statements())
    # entity.reset_bitcoin_data_gen_ai()
    # entity_repo.add_entity(entity)
    # await dbu.sync_gen_ai_statements()


asyncio.run(main())
