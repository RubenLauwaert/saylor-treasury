import asyncio
import logging
from logging import Logger
from pydantic import BaseModel, Field
from typing import List, Optional
from openai import AsyncOpenAI

from modeling.filing.sec_8k.Filing_8K import Filing_8K
from modeling.filing.sec_8k.ItemCode_8K import ItemCode_8K
from modeling.bitcoin_purchase.BitcoinPurchase import BitcoinPurchase
from config import openai_settings


class BitcoinPurchaseResponse(BaseModel):
    contains_bitcoin_purchase: bool = Field(description="Whether the response contains a bitcoin purchase")
    bitcoin_purchase: Optional[BitcoinPurchase] = Field(description="Bitcoin purchase extracted from the response")
    
    class Config:
        extra = "forbid"  # Disallow additional properties

class Bitcoin_Updates_Extractor:
    
    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

  
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.client = openai_settings.get_async_client()
            self.logger.info("AsyncOpenAI client initialized for Bitcoin Updates Extractor")
            self.structured_output_model = openai_settings.structured_output_model
            self.logger.info(f"Using structured output model: {self.structured_output_model}")
            
        except Exception as e:
            self.logger.error(f"Error initializing OpenAI API: {e}")
            


    async def extract_bitcoin_purchases(self, filings_8k: List[Filing_8K]) -> List[BitcoinPurchase]:
        tasks = [self.extract_bitcoin_purchase(filing) for filing in filings_8k]
        return await asyncio.gather(*tasks)
            
            
    async def extract_bitcoin_purchase(self, filing_8k: Filing_8K) -> Optional[BitcoinPurchase]:
        
        # Check if there is an ITEM_8_01 in the filing
        item_8_01 = filing_8k.get_item(ItemCode_8K.ITEM_8_01)
        
        if item_8_01:
            # Use OpenAI (async) to extract bitcoin purchase from the item
            chat_completion = await self.client.beta.chat.completions.parse(
                model=self.structured_output_model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that is used to extract bitcoin purchases from the summarized content of an 8.01 item from an 8-K filing."},
                    {"role": "user", "content": "Can you extract a bitcoin purchase from the following : \n\n" + item_8_01.summary}
                ],
                response_format= BitcoinPurchaseResponse
            )
            
            bitcoin_purchase_response = chat_completion.choices[0].message.parsed
            bitcoin_purchase = bitcoin_purchase_response.bitcoin_purchase
            if bitcoin_purchase:
                return bitcoin_purchase
            else:
                return None     
        else:
            return None
