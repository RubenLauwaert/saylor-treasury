
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
    
    mining_entities = entity_repo.get_bitcoin_mining_entities()
    print([entity.ticker for entity in mining_entities])

    # await dbu.parse_bitcoin_filings()
    

    
asyncio.run(main())
