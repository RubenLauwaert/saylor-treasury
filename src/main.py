import logging
from services.daemon import setup_logging
from services.update_db import DatabaseUpdater

from database import (
    public_entity_collection
)
from data_repositories.sec_filing_metadata_repo import SEC_Filing_Metadata_Repository
from data_repositories.sec_filing_8k_repo import SEC_Filing_8K_Repository
from data_repositories.public_entity_repo import PublicEntityRepository
from config import sec_edgar_settings as ses
import asyncio
import json
import requests
from datetime import date

from services.ai.press_release_extractor import PressReleaseExtractor


setup_logging()

# # metadata repo
# metadata_repo = SEC_Filing_Metadata_Repository(sec_filing_metadatas_collection)
# filings_8k_repo = SEC_Filing_8K_Repository(filings_8k_collection)
# filings_8k = filings_8k_repo.get_filings_for_entity

# Send efts request

main_bitcoin_entity_query = {
    "q": "bitcoin",
    # "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"),
    "category": "custom",
}

main_bitcoin_entity_query_2 = {
    "q": "acquire NEAR(5) bitcoin",
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"),
    "category": "custom",
}

main_bitcoin_entity_query_3 = {
    "q": "add NEAR(5) bitcoin",
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"),
    "category": "custom",
}

# Send efts request

# hits = get_hits_from_queries([main_bitcoin_entity_query])

# DatabaseUpdater
dbu = DatabaseUpdater()

# Public entity repo
entity_repo = PublicEntityRepository(public_entity_collection)


# dbu.sync_bitcoin_entities()


async def main():
    # await dbu.sync_bitcoin_entities()
    
    await dbu.sync_bitcoin_filings()
asyncio.run(main())
