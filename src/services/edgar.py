from typing import List
from config import sec_edgar_settings as ses
from modeling.PublicEntity import PublicEntity
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
