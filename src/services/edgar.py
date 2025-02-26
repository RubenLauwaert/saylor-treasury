from typing import List, Set
from config import sec_edgar_settings as ses
from models.sec_edgar.efts.EFTS_Response import EFTS_Hit, EFTS_Response
from models.sec_edgar.efts.query import *
import logging
import aiohttp
import asyncio
from services.throttler import ApiThrottler

        
# HELPER FUNCTIONS

        
async def _edgar_full_text_search_async(q: dict) -> List[dict]:
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
        
    
async def _get_hits_from_query_async(q: dict) -> List[EFTS_Response]:
    logger = logging.getLogger(__name__)
    responses = await _edgar_full_text_search_async(q)
    efts_responses = [EFTS_Response(**response) for response in responses]
    return efts_responses

async def _get_hits_from_queries_async(queries: List[dict]) -> List[EFTS_Hit]:
    logger = logging.getLogger(__name__)

    hits: List[EFTS_Hit] = []
    for q in queries:
        efts_responses = await _get_hits_from_query_async(q)
        for efts_response in efts_responses:
            hits.extend(efts_response.get_hits())
    logger.info(f"Got {len(hits)} hits from {len(queries)} queries")
    
    return hits



# MAIN METHODS
async def get_raw_content_text(document_url: str) -> str:
    logger = logging.getLogger("SEC_Filing")
    content_html_str = None
    try:

        async with aiohttp.ClientSession(headers=ses.user_agent_header) as session:
            async with session.get(document_url) as response:
                if response.status == 200:
                    content_html_str = await response.text()
                    logger.info(f"Retrieved html content for : {document_url}")
                else:
                    logger.info(
                        f"Failed to retrieve content from {document_url}, status code: {response.status} error: {response.reason}"
                    )
    except Exception as e:
        logger.info(f"Error retrieving content from {document_url}: {e}")

    return content_html_str

async def get_raw_content_text_for(urls: List[str]) -> List[str]:
    """Fetch raw content text for a list of URLs using the throttler."""
    tasks = [lambda url=url: get_raw_content_text(url) for url in urls]  # Wrap calls in lambdas
    return await ApiThrottler.throttle_requests(request_funcs=tasks)


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

async def get_entity_ciks_from_queries_async(queries: List[dict]) -> Set[str]:
    logger = logging.getLogger(__name__)
    hits: List[EFTS_Hit] = await _get_hits_from_queries_async(queries)
    ciks = set([hit.get_source_cik() for hit in hits])
    logger.info(f"Got {len(ciks)} entities from {len(queries)} queries")
    return ciks


async def get_query_result_async(q: dict) -> QueryResult:
    # Get EFTS Hits
    hits = await _get_hits_from_queries_async([q])   
    # Transform to QueryHits
    query_hits = [QueryHit(url=hit.url,
                           score=hit.score,
                           accession_number=hit.source.adsh.replace("-", ""),
                           file_type=hit.get_file_type(), 
                           form_type=hit.get_form_type(), 
                           file_date=hit.get_file_date(), 
                           cik=hit.get_source_cik()) for hit in hits]
    query_result = QueryResult(query=q, hits=query_hits)
    return query_result

async def get_query_results_async(queries: List[dict]) -> QueryResults:
    query_results = []
    for q in queries:
        query_result = await get_query_result_async(q)
        query_results.append(query_result)
    return QueryResults(results=query_results)
    
    
    
