from services.update_db import DatabaseUpdater
from services.daemon import setup_logging

from database import (
    public_entity_collection,
    sec_filing_metadatas_collection,
    filings_8k_collection,
)
from data_repositories.sec_filing_metadata_repo import SEC_Filing_Metadata_Repository
import asyncio

setup_logging()

# # metadata repo
# metadata_repo = SEC_Filing_Metadata_Repository(sec_filing_metadatas_collection)

# filings_424B5 = metadata_repo.get_specific_filing_metadatas_for("KULR", "424B5")


# DatabaseUpdater
dbu = DatabaseUpdater()


dbu.sync_bitcoin_entities()


async def main():
    ticker = "MARA"
    # # Sync 8-k filings for MSTR
    # await dbu.sync_filings_8k_for(ticker)
    # Sync 424B5 filings for MSTR
    await dbu.sync_filings_424B5_for(ticker)
    # # Summarize 8-k filings for MSTR
    # await dbu.summarize_filings_8k_for(ticker)
    # # Update bitcoin purchases
    # await dbu.update_bitcoin_purchases(ticker)


asyncio.run(main())
