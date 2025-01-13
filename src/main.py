from services.update_db import (
    update_sec_filings_for_all_companies,
    update_sec_filings_for_company,
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

# Get MSTR Public Entity
mstr_entity = public_entity_repo.get_entity_by_ticker("MSTR")

# Get latest SEC filing for MSTR
mstr_filings = sec_filing_repo.get_filings_for_entity_after_date(mstr_entity, ImportantDates.MSTR_GENESIS_DATE.value)
filings_8k = [filing for filing in mstr_filings if filing.filing_metadata.form == "8-K"]
sec_filing_w_content = SEC_Filing.from_metadata(filings_8k[0].filing_metadata, include_content=True)
items =sec_filing_w_content.is_parsed