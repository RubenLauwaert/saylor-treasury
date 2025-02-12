from services.update_db import DatabaseUpdater
from services.daemon import setup_logging
from services.edgar import edgar_full_text_search

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

setup_logging()

# metadata repo
metadata_repo = SEC_Filing_Metadata_Repository(sec_filing_metadatas_collection)
filings_8k_repo = SEC_Filing_8K_Repository(filings_8k_collection)
filings_8k = filings_8k_repo.get_filings_for_entity

# Send efts request
q = {
    "q": '"bitcoin" -"bitcoin cash" -"bitcoin sv" -"bitcoin mining"',
    "forms": "8-K",
    "dateRange": "30d",
    "startdt": "2025-01-12",
    "enddt": "2025-02-11",
    "category": "custom",
}
response = edgar_full_text_search(q)
url = response.url
json = response.json()
total_hits = json["hits"]["total"]
aggregations = json["aggregations"]["entity_filter"]

# # DatabaseUpdater
# dbu = DatabaseUpdater()


# dbu.sync_bitcoin_entities()


# async def main():
#     ticker = "TSLA"
#     # # Sync filings 10Q
#     # await dbu.sync_filings_10Q_for(ticker)
#     # # Sync 8-k filings for MSTR
#     # await dbu.sync_filings_8k_for(ticker)
#     # # Sync 424B5 filings for MSTR
#     # await dbu.sync_filings_424B5_for(ticker)
#     # # Summarize 8-k filings for MSTR
#     # await dbu.summarize_filings_8k_for(ticker)
#     # # Update bitcoin purchases
#     # await dbu.update_bitcoin_purchases(ticker)

#     await dbu.sync_filings_8k_for("TZUP")
#     await dbu.update_bitcoin_purchases("TZUP")


# asyncio.run(main())
