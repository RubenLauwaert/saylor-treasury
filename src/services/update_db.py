import logging
from typing import List, Optional
from data_repositories.public_entity_repo import PublicEntityRepository
from data_repositories.sec_filing_repo import SEC_FilingRepository
from modeling.sec_edgar.submissions.SubmissionsRequest import SubmissionsRequest
from modeling.sec_edgar.efts.EFTS_Request import EFTS_Request, EFTS_Response
from modeling.PublicEntity import PublicEntity
from modeling.filing.SEC_Filing import SEC_Filing
from queries import base_bitcoin_8k_company_query
from database import public_entity_collection, filings_collection


def add_new_entities():
    public_entity_repo = PublicEntityRepository(public_entity_collection)
    existing_entities = public_entity_repo.get_all_entities()
    existing_ciks = {entity.cik for entity in existing_entities}
    try:
        efts_response = EFTS_Request(query=base_bitcoin_8k_company_query)
        if efts_response is not None:
            all_entities = efts_response.get_entities()
            new_entities = [
                entity for entity in all_entities if entity.cik not in existing_ciks
            ]
            new_entity_tickers = {new_entity.ticker for new_entity in new_entities}
            if len(new_entities) > 0:
                public_entity_repo.add_entities(new_entities)
                logging.info(
                    f"Added new entities to db with tickers: {new_entity_tickers}"
                )
            else:
                logging.info(f"No new entities to add to db !")
    except Exception as e:
        logging.error(f"Error adding new entities to database: {e}")


def update_sec_filings_for_company(public_entity: PublicEntity):
    filing_repo = SEC_FilingRepository(filings_collection)
    try:
        submission_resp = SubmissionsRequest.from_cik(public_entity.cik).resp_content
        filing_metadatas = submission_resp.filing_metadatas
        sec_filings = [
            SEC_Filing.from_metadata(filing_metadata)
            for filing_metadata in filing_metadatas
        ]
        filing_repo.add_filings(sec_filings)
        logging.info(f"Updated SEC filings for company CIK {public_entity.cik}.")
    except Exception as e:
        logging.error(
            f"Error updating SEC filings for company CIK {public_entity.cik}: {e}"
        )


def update_sec_filings_for_all_companies():
    public_entity_repo = PublicEntityRepository(public_entity_collection)
    try:
        entities = public_entity_repo.get_all_entities()
        for entity in entities:
            update_sec_filings_for_company(entity)
        logging.info("Updated SEC filings for all companies.")
    except Exception as e:
        logging.error(f"Error updating SEC filings for all companies: {e}")
