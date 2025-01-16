from services.update_db import (
    update_sec_filings_for_all_companies,
    sync_filings_for,
)
from services.daemon import setup_logging
from database import filings_collection, public_entity_collection
from data_repositories.sec_filing_repo import SEC_FilingRepository
from data_repositories.public_entity_repo import PublicEntityRepository
from modeling.filing.SEC_Filing import SEC_Filing
from modeling.parsers.SECFilingParser import SEC_Filing_Parser, ItemCode
from util import ImportantDates

setup_logging()

# Data repositories
public_entity_repo = PublicEntityRepository(public_entity_collection)
sec_filing_repo = SEC_FilingRepository(filings_collection)

# Sync filings for
mstr_entity = public_entity_repo.get_entity_by_ticker("KULR")
sync_filings_for(mstr_entity, include_content=True)

# Get latest filing
latest_mstr_filings = sec_filing_repo.get_filings_for_entity(mstr_entity)
latest_mstr_filings_8k = [
    filing
    for filing in latest_mstr_filings
    if filing.filing_metadata.primary_doc_description == "8-K"
]
latest_mstr_filing_8k = latest_mstr_filings_8k[0]
filing_w_content = SEC_Filing.from_metadata(
    latest_mstr_filing_8k.filing_metadata, include_content=True
)
filing_w_content.filing_metadata
filing_w_content.items
