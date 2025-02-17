# FILE: src/events.py

import logging
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from modeling.bitcoin_purchase.BitcoinPurchase import BitcoinPurchase
from modeling.filing.SEC_Filing import SEC_Filing


class BitcoinEvent(BaseModel):
    event_type: Literal[
        "Bitcoin Treasury Update",
        "Total Bitcoin Holdings Statement",
        "Other",
    ] = Field(..., description="The type of event.")
    event_description: str = Field(
        ..., description="A detailed description of the event."
    )
    event_keywords: List[str] = Field(
        description="Keywords related to the event. Avoid keywords with numerical values."
    )

    confidence_score: float = Field(
        description="The confidence score of the event extraction. This is primarily based on the typing of the event."
    )


class BitcoinFilingEventsResult(BaseModel):
    events: List[BitcoinEvent] = Field(
        ...,
        description="The list of extracted filing events. This can be an exhaustive list of all events related to bitcoin in the filing.",
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

    system_prompt = "You are an AI assistant that is used to extract relevant bitcoin events from the the content of an SEC Filing"
    user_prompt = "Can you extract the relevant bitcoin events from the following SEC filing html content : \n\n"

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
        self, filing: SEC_Filing
    ) -> Optional[BitcoinFilingEventsResult]:
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
                        "content": self.user_prompt + filing.content_html_str[0:100000],
                    },
                ],
                response_format=BitcoinFilingEventsResult,
            )

            # Extract the structured output from the response
            result = chat_completion.choices[0].message.parsed
            self.logger.info(f"Structured output: {result}")

            return result

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
