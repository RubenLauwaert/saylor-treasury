# FILE: main.py

import logging
from datetime import date
import warnings
from repositories import PublicEntityRepository
from modeling.sec_edgar.submissions.SubmissionsRequest import SubmissionsRequest
import sec_parser as sp
from sec_downloader import Downloader
from modeling.filing.SEC_Filing import SEC_Filing
from config import sec_edgar_settings as ses
from database import public_entity_collection

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Add entities to database
repository = PublicEntityRepository(public_entity_collection)


# Get entities
entities = repository.get_all_entities()
entity = entities[4]
# Get filings from submissionsRequest for company
submission_resp = SubmissionsRequest.from_cik(entity.cik).resp_content
filing_metadatas_8k = [ filing_metadata for filing_metadata in submission_resp.filing_metadatas if filing_metadata.form == "8-K"]

sec_filing = SEC_Filing.from_metadata(filing_metadatas_8k[0], include_content=True)



# submission_requests = [SubmissionsRequest.from_cik(entity.cik) for entity in entities]


# # download 8-k filings
# sec_downloader = SEC_Downloader()
# submissions_data = sec_downloader.download_8k_filings(ticker, include_content=True)
