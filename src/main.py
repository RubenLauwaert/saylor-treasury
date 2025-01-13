from services.update_db import (
    update_sec_filings_for_all_companies,
    update_sec_filings_for_company,
)
from services.daemon import setup_logging
from database import filings_collection, public_entity_collection
from data_repositories.sec_filing_repo import SEC_FilingRepository
from data_repositories.public_entity_repo import PublicEntityRepository
from util import ImportantDates

setup_logging()

# Data repositories
public_entity_repo = PublicEntityRepository(public_entity_collection)
sec_filing_repo = SEC_FilingRepository(filings_collection)

# Get MSTR Public Entity
mstr_entity = public_entity_repo.get_entity_by_ticker("MSTR")
update_sec_filings_for_all_companies()
