from openai import OpenAI
import logging
from logging import Logger
from typing import List
from config import openai_settings
from modeling.filing.SEC_Filing import SEC_Filing, Item, ItemCode

class ItemSummarizer:
  
  
    client: OpenAI
    summarization_model: str
    logger: Logger
  
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.client = openai_settings.get_client()
            self.logger.info("OpenAI client initialized for ItemSummarizer")
            self.summarization_model = openai_settings.summarization_model
            self.logger.info(f"Using summarization model: {self.summarization_model}")
            
        except Exception as e:
            self.logger.error(f"Error initializing OpenAI API: {e}")
          

    def summarize_items(self, sec_filing: SEC_Filing) -> SEC_Filing:
        for item in sec_filing.items:
            self.logger.info(f"Summarizing item: {item.code}")
            item.summary = self.summarize_item(item.summary)
        return sec_filing

    def summarize_item(self, text: str, item_code: ItemCode = None) -> str:
        summarized_text = text
        try:
          pass
        except Exception as e:
            self.logger.error(f"Error summarizing text: {e}")
        return summarized_text