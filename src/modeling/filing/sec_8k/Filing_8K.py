import asyncio
import aiohttp
from pydantic import BaseModel, Field
from typing import List, Optional
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from modeling.filing.sec_8k.Item_8K import Item_8K
from modeling.parsers.SEC_Filing_Parser_8K import SEC_Filing_Parser_8K
import logging
from config import sec_edgar_settings as ses

class Filing_8K(BaseModel):
    filing_metadata: SEC_Filing_Metadata
    content_html_str: Optional[str] = Field(default=None, description="Content of the filing")
    has_content: bool = Field(default=False, description="Whether the content has been retrieved")
    is_parsed: bool = Field(default=False, description="Whether the content has been parsed")
    is_summarized: bool = Field(default=False, description="Whether the content has been summarized")
    items: List[Item_8K]
    
    @classmethod
    async def from_metadata_async(cls, filing_metadata: SEC_Filing_Metadata, include_content: bool = True):
        logger = logging.getLogger(Filing_8K.__name__)
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
                    items = SEC_Filing_Parser_8K.parse_filing(content_html_str, filing_metadata.items)
                    is_parsed = True
                    logger.info(f"Parsed html content for : {document}")
            except Exception as e:
                logger.info(f"Error retrieving content from {filing_url}: {e}")
        
        return cls(filing_metadata=filing_metadata, 
                   content_html_str=content_html_str, 
                   items=items,
                   is_parsed=is_parsed,
                   has_content=has_raw_content)
        
    @staticmethod
    async def from_metadatas_async(filing_metadatas: List[SEC_Filing_Metadata], include_content: bool = True) -> List['Filing_8K']:
        batch_size = 10
        delay = 1.1  # Slightly more than 1 second to ensure we stay within the limit
        results = []

        for i in range(0, len(filing_metadatas), batch_size):
            batch = filing_metadatas[i:i + batch_size]
            tasks = [Filing_8K.from_metadata_async(filing_metadata, include_content) for filing_metadata in batch]
            results.extend(await asyncio.gather(*tasks))
            if i + batch_size < len(filing_metadatas):
                await asyncio.sleep(delay)

        return results
    
    