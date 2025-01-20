from openai import AsyncOpenAI
import asyncio
import logging
from logging import Logger
from typing import List, Optional
from config import openai_settings
from modeling.filing.sec_8k.Filing_8K import Filing_8K
from modeling.filing.sec_8k.ItemCode_8K import ItemCode_8K
from pydantic import BaseModel, Field


class ItemSummary(BaseModel):
    item_code: ItemCode_8K
    summary: str

class FilingSummary(BaseModel):
    item_summaries: List[ItemSummary]


class Filing_Summarizer_8K:
  
  
    client: AsyncOpenAI
    summarization_model: str
    logger: Logger
    
  
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.client = openai_settings.get_async_client()
            self.logger.info("AsyncOpenAI client initialized for ItemSummarizer")
            self.summarization_model = openai_settings.summarization_model
            self.logger.info(f"Using summarization model: {self.summarization_model}")
            
        except Exception as e:
            self.logger.error(f"Error initializing OpenAI API: {e}")
    
    
    async def summarize_filings_optimized(self, sec_filings: List[Filing_8K]) -> List[Filing_8K]:
        tasks = [self.summarize_filing_optimized(filing) for filing in sec_filings]
        return await asyncio.gather(*tasks)


    
    async def summarize_filing_optimized(self, sec_filing: Filing_8K) -> Filing_8K:
        items = sec_filing.items
        raw_filing_text = " ".join([(item.code + "\n\n" + item.raw_text + "\n\n\n") for item in sec_filing.items])
        try:
            chat_completion = await self.client.beta.chat.completions.parse(
                model=self.summarization_model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that is used for summarizing and cleaning hard to read SEC filings. You should summarize each item of the filing."},
                    {"role": "user", "content": f"Could you summarize the following text from an 8k-SEC filing: \n\n {raw_filing_text}"},
                ],
                max_tokens=2000,
                temperature=0.5,
                response_format=FilingSummary
            )
            filing_summary = chat_completion.choices[0].message.parsed
            self.logger.info(f"Summarized items: {filing_summary.item_summaries}")
            return sec_filing
        except Exception as e:
            self.logger.error(f"Error summarizing text: {e}")
            return sec_filing  # Return the original filing in case of error


    
    
