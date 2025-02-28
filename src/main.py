
from services.daemon import setup_logging
from services.update_db import DatabaseUpdater

from database import (
    public_entity_collection
)

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
    await dbu.sync_bitcoin_entities()
    await dbu.sync_bitcoin_filings()
    await dbu.extract_tenq_xbrl_facts()
    

    
asyncio.run(main())
