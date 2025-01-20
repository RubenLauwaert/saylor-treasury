import logging
from services.update_db import (
    update_sec_filings_for_all_companies,
    sync_filings_for,
    add_new_entities
)
from services.daemon import setup_logging
from database import filings_collection, public_entity_collection
from data_repositories.sec_filing_repo import SEC_FilingRepository
from data_repositories.public_entity_repo import PublicEntityRepository
from modeling.filing.sec_8k.Filing_8K import Filing_8K
from modeling.filing.SEC_Filing import SEC_Filing
from services.ai.Filing_Summarizer_8K import Filing_Summarizer_8K
from util import ImportantDates
import asyncio
import time

setup_logging()



# Data repositories
public_entity_repo = PublicEntityRepository(public_entity_collection)
sec_filing_repo = SEC_FilingRepository(filings_collection)

mstr_entity = public_entity_repo.get_entity_by_ticker("SMLR")
    
# Get latest filing
filings_8k = sec_filing_repo.get_8k_filings_for_after_date(mstr_entity, ImportantDates.MSTR_GENESIS_DATE.value) 
filing_metadatas_8k = [filing.filing_metadata for filing in filings_8k][0:1]
len(filings_8k)


def test_sync():
    start_time = time.time()
    logging.info("Starting to retrieve HTML content for latest filings synchronously.")
    
    filings = [ Filing_8K.from_metadata(metadata, include_content=True) for metadata in filing_metadatas_8k]
    
    end_time = time.time()
    logging.info(f"Finished retrieving HTML content. Time taken: {end_time - start_time} seconds.")
    
    
# test_sync()

async def test_async():
    start_time = time.time()
    logging.info("Starting to retrieve HTML content for latest filings asynchronously.")
    
    # Retrieve html and parse content for latest filings asynchronously
    filings = await Filing_8K.from_metadatas_async(filing_metadatas_8k)
    end_time = time.time()
    logging.info(f"Finished retrieving HTML content. Time taken: {end_time - start_time} seconds.")
    
    
    filing = filings[0]
    url = filing.filing_metadata.document_url
    logging.info(url)
    logging.info(filing.items[1].raw_text)
    # # Summarize filings asynchronously
    # start_time = time.time()
    # summarizer = Filing_Summarizer_8K()
    # summarized_filings = await summarizer.summarize_filings_optimized(filings)
    # summary = summarized_filings[0].items[0].summary
    # logging.info(f"Example Summary: {summary}")
    # end_time = time.time()
    # logging.info(f"Finished summarizing filings. Time taken: {end_time - start_time} seconds.")

    
asyncio.run(test_async())


# # Sync filings for
# mstr_entity = public_entity_repo.get_entity_by_ticker("MSTR")
# sync_filings_for(mstr_entity, include_content=True)

# # Get latest filing
# latest_mstr_filings = sec_filing_repo.get_filings_for_entity(mstr_entity)
# latest_mstr_filings_8k = [
#     filing
#     for filing in latest_mstr_filings
#     if filing.filing_metadata.primary_doc_description == "8-K"
# ]
# latest_mstr_filing_8k = latest_mstr_filings_8k[0]
# filing_w_content = SEC_Filing.from_metadata(
#     latest_mstr_filing_8k.filing_metadata, include_content=True
# )

# filing_w_content.filing_metadata
# filing_w_content.items[0].summary

# # Summarize items in SEC_Filing
# summarizer = ItemSummarizer()
# summarized_filing = summarizer.summarize_items(filing_w_content)

# # Print summarized items
# for item in summarized_filing.items:
#     print(f"Item Code: {item.code}, Summary: {item.summary}")

