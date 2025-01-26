import asyncio
import aiohttp
from pydantic import BaseModel, Field
from typing import List, Optional
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from modeling.filing.sec_8k.Item_8K import Item_8K
from modeling.filing.sec_8k.ItemCode_8K import ItemCode_8K
from modeling.parsers.SEC_Filing_Parser_8K import SEC_Filing_Parser_8K
from modeling.filing.SEC_Filing import SEC_Filing
import logging
from config import sec_edgar_settings as ses


class Filing_8K(SEC_Filing):
    items: List[Item_8K] = Field(default=[], description="Items in the 8-K filing")

    def get_item(self, item_code: ItemCode_8K) -> Optional[Item_8K]:
        for item in self.items:
            if item.code == item_code.value:
                return item
        return None

    @classmethod
    async def from_metadata_async(
        cls, filing_metadata: SEC_Filing_Metadata
    ) -> "Filing_8K":
        logger = logging.getLogger(cls.__name__)

        # Call super method
        sec_filing = await super().from_metadata_async(filing_metadata)

        # Extract 8-k items from the content
        try:
            items = SEC_Filing_Parser_8K.parse_filing(
                sec_filing.content_html_str, item_codes=sec_filing.filing_metadata.items
            )
            is_parsed = True
            return cls(
                **sec_filing.model_dump(exclude={"is_parsed", "items"}),
                is_parsed=is_parsed,
                items=items,
            )

        except Exception as e:
            logger.error(f"Error extracting items from 8-K filing: {e}")

    @staticmethod
    async def from_metadatas_async(
        filing_metadatas: List[SEC_Filing_Metadata],
    ) -> List["Filing_8K"]:
        batch_size = 10
        delay = 1.1  # Slightly more than 1 second to ensure we stay within the limit
        results = []

        for i in range(0, len(filing_metadatas), batch_size):
            batch = filing_metadatas[i : i + batch_size]
            tasks = [
                Filing_8K.from_metadata_async(filing_metadata)
                for filing_metadata in batch
            ]
            results.extend(await asyncio.gather(*tasks))
            if i + batch_size < len(filing_metadatas):
                await asyncio.sleep(delay)

        return results
