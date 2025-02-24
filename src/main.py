import logging
from services.daemon import setup_logging
from services.update_db import DatabaseUpdater

from database import (
    public_entity_collection
)
from data_repositories.sec_filing_metadata_repo import SEC_Filing_Metadata_Repository
from data_repositories.sec_filing_8k_repo import SEC_Filing_8K_Repository
from data_repositories.public_entity_repo import PublicEntityRepository
from config import sec_edgar_settings as ses
import asyncio
import json
import requests
from datetime import date

from services.ai.press_release_extractor import PressReleaseExtractor
from modeling.parsers.sec_10q.XBRL_Parser_10Q import Parser10QXBRL
from modeling.filing.SEC_Filing import SEC_Filing


setup_logging()

# # metadata repo
# metadata_repo = SEC_Filing_Metadata_Repository(sec_filing_metadatas_collection)
# filings_8k_repo = SEC_Filing_8K_Repository(filings_8k_collection)
# filings_8k = filings_8k_repo.get_filings_for_entity

# Send efts request

main_bitcoin_entity_query = {
    "q": "bitcoin",
    # "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"),
    "category": "custom",
}

main_bitcoin_entity_query_2 = {
    "q": "acquire NEAR(5) bitcoin",
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"),
    "category": "custom",
}

main_bitcoin_entity_query_3 = {
    "q": "add NEAR(5) bitcoin",
    "forms": "8-K",
    "dateRange": "custom",
    "startdt": "2020-08-10",
    "enddt": date.today().strftime("%Y-%m-%d"),
    "category": "custom",
}

# Send efts request

# hits = get_hits_from_queries([main_bitcoin_entity_query])

# DatabaseUpdater
dbu = DatabaseUpdater()

# Public entity repo
entity_repo = PublicEntityRepository(public_entity_collection)

# XBRL 10Q parser






# dbu.sync_bitcoin_entities()


async def main():
    # awai  t dbu.sync_bitcoin_entities()
    
    entity = entity_repo.get_entity_by_ticker("MARA")
    filings_10q = entity.get_filing_metadatas_by_form_type("10-Q")
    filing_url = filings_10q[0].document_url.replace(".htm","_htm.xml")
    xbrl_string = await SEC_Filing.get_raw_content_text(filing_url)
    parsed_10q_xbrl = Parser10QXBRL(xbrl_string=xbrl_string, ticker=entity.ticker)
    units = parsed_10q_xbrl.extract_units()
    bitcoin_tags = parsed_10q_xbrl.get_bitcoin_related_tags()
    print(parsed_10q_xbrl.get_bitcoin_summary())
    
asyncio.run(main())
