# FILE: src/events.py

from enum import Enum
import logging
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from modeling.bitcoin_purchase.BitcoinPurchase import BitcoinPurchase
from modeling.filing.SEC_Filing import SEC_Filing
from modeling.parsers.generic.Filing_Parser_Generic import Filing_Parser_Generic


class BitcoinEventType(str, Enum):
    # Bitcoin Transactions
    DEFINITIVE_BITCOIN_ACQUISITION = "Definitive Bitcoin Acquisition - Do not include approvals for an acquisition or sale. Only add events where the acquisition or sale has been completed. "
    DEFINITIVE_BITCOIN_SALE = "Definitive Bitcoin Sale - Do not include approvals for an acquisition or sale. Only add events where the acquisition or sale has been completed.  "
    # Bitcoin Holdings Disclosures
    DISCLOSURE_OF_TOTAL_AMOUNT_OF_BITCOIN = "Definitive Bitcoin Holdings Statement - This event should have a statement reporting total amount of bitcoin held by the entity"
    #Other
    BITCOIN_ANNOUNCEMENT = "Bitcoin Announcement Event"
    BITCOIN_YIELD_STATEMENT = "Bitcoin Yield Metric Statement Event"

class BitcoinEvent(BaseModel):
    event_type: BitcoinEventType = Field(..., description="The type of bitcoin event. "),
    event_description: str = Field(
        ...,
        description="A detailed description of the event. This description should be informative \
            and provide enough context for the event. This description field will be used later to extract structured data."
    )
    event_keywords: List[str] = Field(
        description="Keywords related to the event. Avoid keywords with numerical values."
    )

    confidence_score: float = Field(
        description="The confidence score of the event extraction. This should be a value between 0 and 1. \
            Focus on whether the type of event correctly reflects the content of the event description."
    )


class BitcoinFilingEventsResult(BaseModel):
    events: List[BitcoinEvent] = Field(
        ...,
        description="The list of extracted filing events. This can be an exhaustive list of all events related to bitcoin in the filing.",
    )

class EventsExtractor:

    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

    system_prompt = "You are an AI assistant that is used to extract relevant bitcoin events from the content of an SEC Filing. \
                    This includes events such as Bitcoin Treasury Updates, Total Bitcoin Holdings Statements, \
                    At The Market (ATM), Convertible bond, Preferred Stock issuances and other relevant events"
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
                        "content": self.user_prompt + raw_text[0:127500],
                    },
                ],
                response_format=BitcoinFilingEventsResult,
            )

            # Extract the structured output from the response
            result = chat_completion.choices[0].message.parsed
            return result

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
