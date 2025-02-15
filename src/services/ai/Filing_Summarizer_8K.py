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


    
    async def summarize_filing_optimized(self, filing_8k: Filing_8K) -> Filing_8K:
        items = filing_8k.items
        raw_filing_text = " ".join([(item.code + "\n\n" + item.raw_text + "\n\n\n") for item in filing_8k.items])
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
            # Update the filing with the summarized items
            new_filing_8k = self.update_filing_8k_with_summaries(filing_8k, filing_summary)
            return new_filing_8k
        except Exception as e:
            self.logger.error(f"Error summarizing text: {e}")
            return filing_8k  # Return the original filing in case of error
        
        
    def update_filing_8k_with_summaries(self, filing_8k: Filing_8K, filing_summary: FilingSummary) -> Filing_8K:
        updated_filing_8k = filing_8k
        item_summaries = filing_summary.item_summaries
        new_items = []
        
        for item in filing_8k.items:
            for item_summary in item_summaries:
                if item.code == item_summary.item_code.value:
                    item.summary = item_summary.summary
                    new_items.append(item)
                    break
        
        updated_filing_8k.items = new_items
        updated_filing_8k.is_summarized = True
        return updated_filing_8k


    
    
