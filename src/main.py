from services.update_db import DatabaseUpdater
from services.daemon import setup_logging
from services.edgar import get_hits_from_queries_async, get_hits_from_queries

from database import (
    public_entity_collection,
    sec_filing_metadatas_collection,
    filings_8k_collection,
)
from data_repositories.sec_filing_metadata_repo import SEC_Filing_Metadata_Repository
from data_repositories.sec_filing_8k_repo import SEC_Filing_8K_Repository
from config import sec_edgar_settings as ses
import asyncio
import json
import requests
from datetime import date


setup_logging()

# metadata repo
metadata_repo = SEC_Filing_Metadata_Repository(sec_filing_metadatas_collection)
filings_8k_repo = SEC_Filing_8K_Repository(filings_8k_collection)
filings_8k = filings_8k_repo.get_filings_for_entity

# Send efts request

main_bitcoin_entity_query = {
    "q": 'bitcoin',
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"), 
    "category": "custom",
}

main_bitcoin_entity_query_2 = {
    "q": 'acquire NEAR(5) bitcoin',
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"), 
    "category": "custom",
}

main_bitcoin_entity_query_3 = {
    "q": 'add NEAR(5) bitcoin',
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"), 
    "category": "custom",
}

# Send efts request




# hits = get_hits_from_queries([main_bitcoin_entity_query])

# # DatabaseUpdater
# dbu = DatabaseUpdater()


# dbu.sync_bitcoin_entities()


async def main():
    hits = await get_hits_from_queries_async([main_bitcoin_entity_query])


asyncio.run(main())
