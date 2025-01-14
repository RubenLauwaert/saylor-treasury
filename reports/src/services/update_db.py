import logging
from datetime import date
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


def sync_filings_for(public_entity: PublicEntity, include_content: bool = False):
    filing_repo = SEC_FilingRepository(filings_collection)
    latest_filing_date = filing_repo.get_latest_filing_date_for(public_entity)
    try:
        submission_resp = SubmissionsRequest.from_cik(public_entity.cik).resp_content
        filing_metadatas = submission_resp.filing_metadatas
        new_sec_filings = [
            SEC_Filing.from_metadata(filing_metadata, include_content=include_content)
            for filing_metadata in filing_metadatas
        if date.fromisoformat(filing_metadata.filing_date) > latest_filing_date]
        logging.info(f"Retrieved {len(new_sec_filings)} new SEC filings for company CIK {public_entity.cik}.")
        filing_repo.add_filings(new_sec_filings)
        logging.info(f"Synced SEC filings for company CIK {public_entity.cik}.")
    except Exception as e:
        logging.error(
            f"Error updating SEC filings for company CIK {public_entity.cik}: {e}"
        )


def update_sec_filings_for_all_companies():
    public_entity_repo = PublicEntityRepository(public_entity_collection)
    try:
        entities = public_entity_repo.get_all_entities()
        for entity in entities:
            sync_filings_for(entity)
        logging.info("Updated SEC filings for all companies.")
    except Exception as e:
        logging.error(f"Error updating SEC filings for all companies: {e}")
