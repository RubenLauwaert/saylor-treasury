# FILE: main.py

import logging
from datetime import date
from repositories import PublicEntityRepository
from modeling.sec_edgar.submissions.SubmissionsRequest import SubmissionsRequest
from database import public_entity_collection

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Add entities to database
repository = PublicEntityRepository(public_entity_collection)


# Get entities
entities = repository.get_all_entities()
entity = entities[0]
submission_resp = SubmissionsRequest.from_cik(entity.cik).resp_content
length_filings = len(submission_resp.filings)
filing = submission_resp.filings[length_filings - 1].model_dump()
# submission_requests = [SubmissionsRequest.from_cik(entity.cik) for entity in entities]


# # download 8-k filings
# sec_downloader = SEC_Downloader()
# submissions_data = sec_downloader.download_8k_filings(ticker, include_content=True)
