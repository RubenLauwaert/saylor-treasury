# FILE: main.py

import logging
import requests
from datetime import date
from modeling.efts.EFTS_Request import EFTS_Request
from modeling.PublicEntity import PublicEntity, PublicEntityType
from modeling.filing.SEC_Downloader import SEC_Downloader
from repositories import PublicEntityRepository
from database import public_entity_collection
from config import sec_edgar_settings

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Add entities to database
repository = PublicEntityRepository(public_entity_collection)


# Get entity by ticker
ticker = "RIOT"
entity = repository.get_entity_by_ticker(ticker)
cik = entity.cik if entity else None


# download 8-k filings
sec_downloader = SEC_Downloader()
submissions_data = sec_downloader.download_8k_filing_metadatas(cik)
