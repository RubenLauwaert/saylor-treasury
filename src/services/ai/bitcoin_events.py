# FILE: src/events.py

from enum import Enum
import logging
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from models.bitcoin_purchase.BitcoinPurchase import BitcoinPurchase
from models.filing.SEC_Filing import SEC_Filing
from models.parsers.generic.Filing_Parser_Generic import Filing_Parser_Generic
from models.util import *


class EventsExtractor:

    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

    system_prompt = "You are an AI assistant that is used to extract relevant events from SEC filings, particularly 8-K filings and the Exhibits belonging to 8-K's"
    user_prompt = "Can you extract all events, relevant for understanding their bitcoin strategy, from the following SEC filing html content : \n\n"

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

    async def extract_events(
        self, raw_text: str
    ) -> Optional[StatementResults]:
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
                        "content": self.user_prompt + raw_text[0:127500],
                    },
                ],
                response_format=StatementResults,
            )

            # Extract the structured output from the response
            result = chat_completion.choices[0].message.parsed
            return result

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
