from services.update_db import DatabaseUpdater
from services.daemon import setup_logging
from services.ai.Filing_Summarizer_8K import Filing_Summarizer_8K
from database import filings_8k_collection, public_entity_collection
from data_repositories.sec_filing_8k_repo import SEC_Filing_8K_Repository
from data_repositories.public_entity_repo import PublicEntityRepository
import asyncio
setup_logging()

# DatabaseUpdater
dbu = DatabaseUpdater()


dbu.sync_bitcoin_entities() 

async def main():
    ticker = "SMLR"
    # Sync 8-k filings for MSTR
    await dbu.sync_filings_8k_for(ticker)
    # Summarize 8-k filings for MSTR
    await dbu.summarize_filings_8k_for(ticker)
    # Update bitcoin purchases
    await dbu.update_bitcoin_purchases(ticker)
    


asyncio.run(main())



