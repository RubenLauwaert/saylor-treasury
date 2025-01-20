from pydantic import BaseModel, Field
from typing import Mapping, Optional
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from modeling.parsers.SECFilingParser import *
import logging
import aiohttp
import asyncio
from sec_downloader import Downloader
from config import sec_edgar_settings as ses

class SEC_Filing(BaseModel):
    filing_metadata: SEC_Filing_Metadata = Field(description="Metadata of the given filing")
    content_html_str: Optional[str] = Field(default=None, description="Content of the filing")
    is_parsed: bool = Field(default=False, description="Whether the content has been parsed")
    has_raw_content: bool = Field(default=False, description="Whether the content has been retrieved")
    items: Optional[List[Item]] = Field(default=[], description="Items extracted from the filing")

    @classmethod
    def from_metadata(cls, filing_metadata: SEC_Filing_Metadata, include_content: bool = False):
        logger = logging.getLogger(SEC_Filing.__name__)
        content_html_str = None    
        items = []
        is_parsed = False
        has_raw_content = False
        if include_content:
            try:
                # Retrieve raw html content
                dl = Downloader(ses.user_agent_header, ses.sec_user_agent_email)
                filing_url = filing_metadata.document_url
                document = filing_metadata.primary_document
                content_html_str = dl.download_filing(url=filing_url).__str__()
                has_raw_content = True
                logger.info(f"Retrieved html content : {document}")
                # Parse raw html content into list of items
                items = SEC_Filing_Parser.parse_filing(content_html_str, filing_metadata.items)
                is_parsed = True
                logger.info(f"Parsed html content for : {document}")
            except Exception as e:
                logger.info(f"Error retrieving content from {filing_url}: {e}")
        
        return cls(filing_metadata=filing_metadata, 
                   content_html_str=content_html_str, 
                   items=items,
                   is_parsed=is_parsed,
                   has_raw_content=has_raw_content)
        
    @classmethod
    async def from_metadata_async(cls, filing_metadata: SEC_Filing_Metadata, include_content: bool = True):
        logger = logging.getLogger(SEC_Filing.__name__)
        content_html_str = None    
        items = []
        is_parsed = False
        has_raw_content = False
        if include_content:
            try:
                # Retrieve raw html content
                filing_url = filing_metadata.document_url
                document = filing_metadata.primary_document
                headers = {"User-Agent": f"{ses.user_agent_header} ({ses.sec_user_agent_email})"}
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(filing_url) as response:
                        if response.status == 200:
                            content_html_str = await response.text()
                            has_raw_content = True
                            logger.info(f"Retrieved html content : {document}")
                        else:
                            logger.info(f"Failed to retrieve content from {filing_url}, status code: {response.status} error: {response.reason}")
                # Parse raw html content into list of items
                if content_html_str:
                    items = SEC_Filing_Parser.parse_filing(content_html_str, filing_metadata.items)
                    is_parsed = True
                    logger.info(f"Parsed html content for : {document}")
            except Exception as e:
                logger.info(f"Error retrieving content from {filing_url}: {e}")
        
        return cls(filing_metadata=filing_metadata, 
                   content_html_str=content_html_str, 
                   items=items,
                   is_parsed=is_parsed,
                   has_raw_content=has_raw_content)
        
    @staticmethod
    async def from_metadatas_async(filing_metadatas: List[SEC_Filing_Metadata], include_content: bool = True) -> List['SEC_Filing']:
        tasks = [SEC_Filing.from_metadata_async(filing_metadata, include_content) for filing_metadata in filing_metadatas]
        return await asyncio.gather(*tasks)