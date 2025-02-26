# FILE: src/events.py

from enum import Enum
import logging
from tokenize import String
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings


class TagResult(BaseModel):
  tag: Optional[str]
  confidence: float 


class XBRL_Extractor:

    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

    system_prompt = "You are an expert in XBRL financial reporting."

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        try:
            self.client = openai_settings.get_async_client()
            self.logger.info(
                "AsyncOpenAI client initialized for Bitcoin Updates Extractor"
            )
            self.structured_output_model = openai_settings.structured_output_model
            self.logger.info(
                f"Using structured output model: {self.structured_output_model}"
            )
            
            

        except Exception as e:
            self.logger.error(f"Error initializing OpenAI API: {e}")

    async def extract_tag(
        self, xbrl_tags: set[str], user_prompt: str
    ) -> Optional[TagResult]:
        try:
            chat_completion = await self.client.beta.chat.completions.parse(
                model=self.structured_output_model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                response_format=TagResult,
            )

            # Extract the structured output from the response
            result = chat_completion.choices[0].message.parsed
            return result

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
            
    def extract_total_bitcoin_holdings_tag(self, xbrl_tags: set[str]) -> TagResult:
        user_prompt = self.generate_prompt_bitcoin_holdings(xbrl_tags)
        return self.extract_tag(xbrl_tags, user_prompt)
      
    def extract_total_bitcoin_fair_value_tag(self, xbrl_tags: set[str]) -> TagResult:
        user_prompt = self.generate_prompt_bitcoin_fair_value(xbrl_tags)
        return self.extract_tag(xbrl_tags, user_prompt)
      
    def extract_total_bitcoin__cost_basis_tag(self, xbrl_tags: set[str]) -> TagResult:
        user_prompt = self.generate_prompt_total_bitcoin_cost_basis(xbrl_tags)
        return self.extract_tag(xbrl_tags, user_prompt)
            
    # Prompt generators
            
            
    def generate_prompt_bitcoin_holdings(self, xbrl_tags: set[str]) -> str:
        prompt = f"""
        You are an AI expert in financial reporting. Given the following XBRL tags, your task is to determine 
        which tag represents the total Bitcoin holdings of the entity.

        Selection criteria:
        1. The tag should indicate the total number of Bitcoin or cryptocurrency units the company owns as an investment.
        2. It should **not** refer to fair value, cost, sales, purchases, borrowings, collateral, or gains/losses or bitcoin held for its customers (crypto providers).
        3. Tags containing "NumberOfUnits", "Held", or "Balance" are highly preferred.
        4. If multiple tags fit, pick the **most relevant one**.
        5. Avoid tags cointaining "TextBlock"

      

        Here are the available XBRL tags:
        {xbrl_tags}

        Return only the most relevant XBRL tag.
        
        If no such tag exists, return None for the tag and let it show in the confidence score by giving it a 0 score.
        """
        
        return prompt
        
        
    def generate_prompt_bitcoin_fair_value(self, xbrl_tags: set[str]) -> str:
        prompt = f"""
        You are an AI expert in financial reporting. Given the following XBRL tags, your task is to determine 
        which tag represents the fair value of the total Bitcoin holdings of the entity.

        Selection criteria:
        1. The tags containing the words "Fair", "Value" are highly preferred.
        2. The tags should have words referring to the bitcoin holdings, example: ["Bitcoin","Crypto","DigitalAsset","IntangibleAsset"].
        3. Avoid collateral, sales, purchases and gains/losses tags , change, unrealized gains.
        3. If multiple tags fit, pick the **most relevant one**.


        Here are the available XBRL tags:
        {xbrl_tags}
        
        If no such tag exists, return None for the tag and let it show in the confidence score by giving it a 0 score.
        """
        return prompt
      
    def generate_prompt_total_bitcoin_cost_basis(self, xbrl_tags: set[str]) -> str:
      prompt = f"""
      You are an AI expert in financial reporting. Given the following XBRL tags, your task is to determine 
      which tag represents the cost basis of the total Bitcoin holdings of the entity.

      Selection criteria:
      1. The tag should indicate the total cost basis of the bitcoin that the company holds as an investment.
      2. It should **not** refer to seperate bitcoin purchases.
      3. Tags containing "Cost" and a link to bitcoin with the words ["Bitcoin","Crypto","DigitalAsset","IntangibleAsset"] are a big plus.
      4. If multiple tags fit, pick the **most relevant one**.
      5. Avoid tags cointaining "TextBlock"
    

      Here are the available XBRL tags:
      {xbrl_tags}

      Return only the most relevant XBRL tag.
      
      If no such tag exists, return None for the tag and let it show in the confidence score by giving it a 0 score.
      """
      return prompt
