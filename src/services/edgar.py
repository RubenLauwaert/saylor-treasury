from typing import List
from config import sec_edgar_settings as ses
from modeling.PublicEntity import PublicEntity
from modeling.sec_edgar.efts.EFTS_Response import EFTS_Hit, EFTS_Response
import requests
import logging


def retrieve_public_entities() -> List[PublicEntity]:
    public_entities = []
    url_str = ses.company_tickers_url
    request_header = ses.user_agent_header
    response = requests.get(url=url_str, headers=request_header)

    if response.status_code == 200:
        tickers_and_ciks = response.json()
        for entity in tickers_and_ciks.values():
            cik = str(entity["cik_str"]).zfill(10)
            ticker = entity["ticker"]
            title = entity["title"]
            public_entities.append(PublicEntity(name=title, ticker=ticker, cik=cik))
    else:
        raise Exception(
            f"Failed to retrieve public entities -  Status code { response.status }"
        )

    return public_entities


def retrieve_submissions_for_entity(cik: str):
    url_str = ses.get_formatted_entity_submissions_url(cik=cik)
    request_header = ses.user_agent_header
    # Make request
    response = requests.get(url=url_str, headers=request_header)

    if response.status_code == 200:
        result = response.json()
        return result
    else:
        raise Exception(
            f"Failed to retrieve submissions for entity {cik} - Status code { response.status }"
        )


def edgar_full_text_search(q: dict) -> requests.Response:
    url_str = ses.base_efts_url
    request_header = ses.user_agent_header
    response = requests.get(url=url_str, params=q, headers=request_header)

    if response.status_code == 200:
        return response
    else:
        raise Exception(
            f"Failed to retrieve full text search results - Status code { response.status }"
        )
        

def get_hits_from_query(q: dict) -> EFTS_Response:
    logger = logging.getLogger(__name__)
    response = edgar_full_text_search(q)
    efts_result = EFTS_Response(**response.json())
    return efts_result

def get_hits_from_queries(queries: List[dict]) -> List[EFTS_Hit]:
    logger = logging.getLogger(__name__)

    hits: List[EFTS_Hit] = []
    for q in queries:
        efts_result = get_hits_from_query(q)
        hits += efts_result.get_hits()
    logger.info(f"Got {len(hits)} hits from {len(queries)} queries")
    
    ciks = set([hit.get_source_cik() for hit in hits])
    display_names = set([hit.get_source_name() for hit in hits])
    urls = set([hit.get_url() for hit in hits])
    # file_descriptions = set([hit.get_file_description() for hit in hits])
    file_types = [hit.get_file_type() for hit in hits]
    logger.info(ciks)
    logger.info(display_names)
    logger.info(urls)
    logger.info(file_types)
    return hits
    
    
    
    
