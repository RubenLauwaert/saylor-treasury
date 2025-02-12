from typing import List, Set
from config import sec_edgar_settings as ses
from modeling.sec_edgar.efts.EFTS_Response import EFTS_Hit, EFTS_Response
import requests
import logging
import time
import aiohttp
import asyncio


# def retrieve_public_entities() -> List[PublicEntity]:
#     public_entities = []
#     url_str = ses.company_tickers_url
#     request_header = ses.user_agent_header
#     response = requests.get(url=url_str, headers=request_header)

#     if response.status_code == 200:
#         tickers_and_ciks = response.json()
#         for entity in tickers_and_ciks.values():
#             cik = str(entity["cik_str"]).zfill(10)
#             ticker = entity["ticker"]
#             title = entity["title"]
#             public_entities.append(PublicEntity(name=title, ticker=ticker, cik=cik))
#     else:
#         raise Exception(
#             f"Failed to retrieve public entities -  Status code { response.status }"
#         )

#     return public_entities


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
        
async def retrieve_submissions_for_entity_async(cik: str) -> dict:
    url_str = ses.get_formatted_entity_submissions_url(cik=cik)
    request_header = ses.user_agent_header

    async with aiohttp.ClientSession() as session:
        async with session.get(url=url_str, headers=request_header) as response:
            if response.status == 200:
                result = await response.json()
                return result
            else:
                raise Exception(
                    f"Failed to retrieve submissions for entity {cik} - Status code {response.status}"
                )


def edgar_full_text_search(q: dict) -> List[requests.Response]:
    logger = logging.getLogger(__name__)
    responses = []
    url_str = ses.base_efts_url
    request_header = ses.user_agent_header
    first_response = requests.get(url=url_str, params=q, headers=request_header)
    
    if first_response.status_code == 200:
        responses.append(first_response)
        result = first_response.json()
        amt_hits = result["hits"]["total"]["value"]
        logger.info(f"Got {amt_hits} hits")
        if amt_hits > 100:
            for i in range(100, amt_hits, 100):
                logger.info(f"Getting hits from {i} to {i+100}")
                q["from"] = i
                time.sleep(0.11)  # Adding a wait time of 0.11 seconds
                response = requests.get(url=url_str, params=q, headers=request_header)
                if response.status_code == 200:
                    responses.append(response)
        logger.info(f"Got {len(responses)} responses")
        return responses
    else:
        raise Exception(
            f"Failed to retrieve full text search results - Status code { first_response.status }"
        )
        
async def edgar_full_text_search_async(q: dict) -> List[dict]:
    logger = logging.getLogger(__name__)
    responses = []
    url_str = ses.base_efts_url
    request_header = ses.user_agent_header

    async with aiohttp.ClientSession() as session:
        async def fetch(session, url, params, headers):
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to retrieve full text search results - Status code {response.status}")

        first_response = await fetch(session, url_str, q.copy(), request_header)
        responses.append(first_response)
        amt_hits = first_response["hits"]["total"]["value"]
        logger.info(f"Got {amt_hits} hits")

        if amt_hits > 100:
            tasks = []
            for i in range(100, amt_hits, 100):
                logger.info(f"Getting hits from {i} to {i+100}")
                q_copy = q.copy()
                q_copy["from"] = i
                tasks.append(fetch(session, url_str, q_copy, request_header))
                if len(tasks) == 10:
                    await asyncio.sleep(1)  # Wait for 1 second to adhere to rate limit
                    responses.extend(await asyncio.gather(*tasks))
                    tasks = []

            if tasks:
                await asyncio.sleep(1)  # Wait for 1 second to adhere to rate limit
                responses.extend(await asyncio.gather(*tasks))

        logger.info(f"Got {len(responses)} responses")
        return responses
        

def get_hits_from_query(q: dict) -> List[EFTS_Response]:
    logger = logging.getLogger(__name__)
    responses = edgar_full_text_search(q)
    efts_responses= [EFTS_Response(**response.json()) for response in responses]
    return efts_responses

def get_hits_from_queries(queries: List[dict]) -> List[EFTS_Hit]:
    logger = logging.getLogger(__name__)

    hits: List[EFTS_Hit] = []
    for q in queries:
        efts_responses = get_hits_from_query(q)
        for efts_response in efts_responses:
            hits.extend(efts_response.get_hits())
    logger.info(f"Got {len(hits)} hits from {len(queries)} queries")
    return hits
    
    
async def get_hits_from_query_async(q: dict) -> List[EFTS_Response]:
    logger = logging.getLogger(__name__)
    responses = await edgar_full_text_search_async(q)
    efts_responses = [EFTS_Response(**response) for response in responses]
    return efts_responses

async def get_hits_from_queries_async(queries: List[dict]) -> List[EFTS_Hit]:
    logger = logging.getLogger(__name__)

    hits: List[EFTS_Hit] = []
    for q in queries:
        efts_responses = await get_hits_from_query_async(q)
        for efts_response in efts_responses:
            hits.extend(efts_response.get_hits())
    logger.info(f"Got {len(hits)} hits from {len(queries)} queries")
    
    return hits

async def get_entity_ciks_from_queries_async(queries: List[dict]) -> Set[str]:
    logger = logging.getLogger(__name__)
    hits: List[EFTS_Hit] = await get_hits_from_queries_async(queries)
    ciks = set([hit.get_source_cik() for hit in hits])
    logger.info(f"Got {len(ciks)} entities from {len(queries)} queries")
    return ciks
    
    
    
