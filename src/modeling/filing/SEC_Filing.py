from pydantic import BaseModel, Field
from typing import List, Optional
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from config import sec_edgar_settings as ses
import logging

# Async behavior
import aiohttp
import asyncio


class SEC_Filing(BaseModel):
    filing_metadata: SEC_Filing_Metadata
    content_html_str: Optional[str] = Field(
        default=None, description="Content of the filing"
    )
    has_content: bool = Field(
        default=False, description="Whether the content has been retrieved"
    )
    is_parsed: bool = Field(
        default=False, description="Whether the content has been parsed"
    )
    is_summarized: bool = Field(
        default=False, description="Whether the content has been summarized"
    )

    @classmethod
    async def from_metadata_async(
        cls, filing_metadata: SEC_Filing_Metadata
    ) -> "SEC_Filing":
        logger = logging.getLogger(cls.__name__)
        content_html_str = None
        is_parsed = False
        has_raw_content = False

        try:
            # Retrieve raw html content
            filing_url = filing_metadata.document_url
            document = filing_metadata.primary_document
            async with aiohttp.ClientSession(headers=ses.user_agent_header) as session:
                async with session.get(filing_url) as response:
                    if response.status == 200:
                        content_html_str = await response.text()
                        has_raw_content = True
                        logger.info(f"Retrieved html content : {document}")
                    else:
                        logger.info(
                            f"Failed to retrieve content from {filing_url}, status code: {response.status} error: {response.reason}"
                        )
        except Exception as e:
            logger.info(f"Error retrieving content from {filing_url}: {e}")

        return cls(
            filing_metadata=filing_metadata,
            content_html_str=content_html_str,
            is_parsed=is_parsed,
            has_content=has_raw_content,
        )

    @staticmethod
    async def from_metadatas_async(
        filing_metadatas: List[SEC_Filing_Metadata],
    ) -> List["SEC_Filing"]:
        batch_size = 10
        delay = 1.1  # Slightly more than 1 second to ensure we stay within the limit
        results = []

        for i in range(0, len(filing_metadatas), batch_size):
            batch = filing_metadatas[i : i + batch_size]
            tasks = [
                SEC_Filing.from_metadata_async(filing_metadata)
                for filing_metadata in batch
            ]
            results.extend(await asyncio.gather(*tasks))
            if i + batch_size < len(filing_metadatas):
                await asyncio.sleep(delay)

        return results

    @staticmethod
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
    
    @staticmethod
    async def get_raw_content_text_for(urls: List[str]) -> List[str]:
        raw_contents = []
        batch_size = 10  # Number of requests per batch
        delay = 1.1  # Delay in seconds between batches
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            results = await asyncio.gather(*(SEC_Filing.get_raw_content_text(url) for url in batch))
            raw_contents.extend(results)
            if i + batch_size < len(urls):
                await asyncio.sleep(delay)  # Wait for 1 second between batches

        return raw_contents

    def __str__(self):
        document_url = self.filing_metadata.document_url
        primary_document = self.filing_metadata.primary_document
        cik = self.filing_metadata.company_cik
        filing_date = self.filing_metadata.filing_date
        accession_number = self.filing_metadata.accession_number
        return f"\n- Document URL: {document_url} \n- Primary document : {primary_document} \n- Filing date : {filing_date}\n"
