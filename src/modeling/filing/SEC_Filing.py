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
            async with aiohttp.ClientSession(
                headers=ses.user_agent_header()
            ) as session:
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
