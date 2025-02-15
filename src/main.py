from services.daemon import setup_logging
from modeling.PublicEntity import PublicEntity
from services.edgar import get_entity_ciks_from_queries_async

from database import (
    public_entity_collection,
    sec_filing_metadatas_collection,
    filings_8k_collection,
)
from data_repositories.sec_filing_metadata_repo import SEC_Filing_Metadata_Repository
from data_repositories.sec_filing_8k_repo import SEC_Filing_8K_Repository
from data_repositories.public_entity_repo import PublicEntityRepository
from config import sec_edgar_settings as ses
import asyncio
import json
import requests
from datetime import date


setup_logging()

# # metadata repo
# metadata_repo = SEC_Filing_Metadata_Repository(sec_filing_metadatas_collection)
# filings_8k_repo = SEC_Filing_8K_Repository(filings_8k_collection)
# filings_8k = filings_8k_repo.get_filings_for_entity

# Send efts request

main_bitcoin_entity_query = {
    "q": "bitcoin",
    "forms": "8-K",
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

# # DatabaseUpdater
# dbu = DatabaseUpdater()


# dbu.sync_bitcoin_entities()


async def main():
    # cik = "0001050446"  # CIK for MicroStrategy Incorporated (MSTR)
    # entity = await PublicEntity.from_cik(cik)

    # # Get bitcoin entity ciks
    # bitcoin_entity_ciks = await get_entity_ciks_from_queries_async([main_bitcoin_entity_query])

    # # Generate entities from ciks
    # bitcoin_entities = await PublicEntity.from_ciks(bitcoin_entity_ciks)

    # Add public entity to the database
    entity_repo = PublicEntityRepository(public_entity_collection)

    # retrieve entity
    entity = entity_repo.get_entity_by_ticker("SMLR")
    updated_entity = await entity.update_bitcoin_filing_hits()
    entity_repo.add_entity(updated_entity)


asyncio.run(main())
