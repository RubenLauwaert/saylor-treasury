from services.update_db import DatabaseUpdater
from services.daemon import setup_logging
import asyncio
setup_logging()

# DatabaseUpdater
dbu = DatabaseUpdater()



async def main():
    # Sync 8-k filings for MSTR
    await dbu.sync_filings_8k_for("MSTR")


asyncio.run(main())



