# FILE: src/events.py

import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from modeling.bitcoin_purchase.BitcoinPurchase import BitcoinPurchase
from modeling.filing.SEC_Filing import SEC_Filing


class FilingEvent(BaseModel):
    event_type: str = Field(..., description="The type of the filing event.")
    event_date: str = Field(..., description="The date of the filing event.")
    event_description: str = Field(
        ..., description="The description of the filing event."
    )

    bitcoin_related: bool = Field(
        ..., description="Whether the event is bitcoin-related."
    )


class FilingEventsResult(BaseModel):
    events: List[FilingEvent] = Field(
        ..., description="The list of extracted filing events."
    )
    contains_bitcoin_purchase: bool = Field(
        description="Whether the filing contains information about a bitcoin purchase"
    )
    bitcoin_purchase: Optional[BitcoinPurchase] = Field(
        description="The bitcoin purchase event, if applicable."
    )


class EventsExtractor:

    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

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

    async def extract_events(self, filing: SEC_Filing) -> Optional[FilingEventsResult]:
        try:
            chat_completion = await self.client.beta.chat.completions.parse(
                model=self.structured_output_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that is used to extract events from the url of an SEC filing.",
                    },
                    {
                        "role": "user",
                        "content": "Can you extract events from the following filing html content : \n\n"
                        + filing.content_html_str,
                    },
                ],
                response_format=FilingEventsResult,
            )

            # Extract the structured output from the response
            result = chat_completion.choices[0].message.parsed
            self.logger.info(f"Structured output: {result}")

            return result

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
