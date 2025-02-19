# FILE: src/events.py

import logging
from pydantic import BaseModel, Field, model_validator
from typing import List, Literal, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from services.ai.bitcoin_events import *



class BitcoinTreasuryUpdate(BaseModel):
    type: Literal["Purchase", "Sale"]
    
    bitcoin_amount: Optional[float] = Field(
        None, description="The amount of bitcoin acquired or sold. If this value is not explicitly stated in the input but inferred or calculated, set 'bitcoin_amount_filled_in' to True."
    )
    average_price_per_bitcoin: Optional[int] = Field(
        None, description="The average price per bitcoin for the acquisition or sale. If this value is not explicitly stated in the input but inferred or calculated, set 'average_price_per_bitcoin_filled_in' to True."
    )
    amount_in_usd: Optional[int] = Field(
        None, description="The total amount in USD spent or received for the acquisition or sale. If this value is not explicitly stated in the input but inferred or calculated, set 'amount_in_usd_filled_in' to True."
    )

    # Flags for whether AI inferred values
    bitcoin_amount_filled_in: bool = Field(
        ..., description="Set to True if 'bitcoin_amount' was inferred or calculated instead of being explicitly found in the input."
    )
    
    average_price_per_bitcoin_filled_in: bool = Field(
        ..., description="Set to True if 'average_price_per_bitcoin' was inferred or calculated instead of being explicitly found in the input."
    )
    
    amount_in_usd_filled_in: bool = Field(
        ..., description="Set to True if 'amount_in_usd' was inferred or calculated instead of being explicitly found in the input."
    )


    @model_validator(mode='before')
    def check_either_bitcoin_amount_or_amount_in_usd(cls, values):
        bitcoin_amount = values.get('bitcoin_amount')
        amount_in_usd = values.get('amount_in_usd')
        average_price_per_bitcoin = values.get('average_price_per_bitcoin')

        if bitcoin_amount is None:
            raise ValueError("Bitcoin amount or amount in dollars must be present.")

        return values


class TotalBitcoinHoldings(BaseModel):
    total_bitcoin_holdings: Optional[float] = Field(
         ..., description="The total amount of bitcoin held by the entity"
    )
    average_price_per_bitcoin: Optional[int] = Field(
        ..., description="The average price per bitcoin for the total bitcoin holdings"
    )
    total_amount_in_usd: Optional[int] = Field(
        ..., description="The total amount of dollars spent for the total bitcoin holdings"
    )
    
    @model_validator(mode='before')
    def check_fields(cls, values):
        total_bitcoin_holdings = values.get('total_bitcoin_holdings')
        average_price_per_bitcoin = values.get('average_price_per_bitcoin')
        total_amount_in_usd = values.get('total_amount_in_usd')

        if total_bitcoin_holdings is None:
            raise ValueError("The total amount of bitcoin held by the entity must be provided.")

        return values


class EventsTransformer:

    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

    system_prompt = "You are an AI assistant that is used to transform extracted events from an SEC Filing into structured data. \
        Avoid guessing or making assumptions. Only use the information provided in the events to build the structured output."
        

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
            
    # Getters
    
    def get_user_prompt(self, events: List[BitcoinEvent], event_type: BitcoinEventType ) -> Optional[str]:
        filtered_events = [event for event in events if event.event_type == event_type]
        if(event_type == BitcoinEventType.DEFINITIVE_BITCOIN_ACQUISITION):
            return f"Given the following extracted definitive Bitcoin acquisition events: \n\n {filtered_events} \
                \n\n Your job is to pick out the event that is most accurate and relevant \
                    for building the structured output and then transform it into the desired structured data."
        elif(event_type == BitcoinEventType.DEFINITIVE_BITCOIN_SALE):
            return f"Given the following extracted definitive Bitcoin sale events: \n\n {filtered_events} \
                \n\n Your job is to pick out the event that is most accurate and relevant \
                    for building the structured output and then transform it into the desired structured data."
        elif(event_type == BitcoinEventType.DISCLOSURE_OF_TOTAL_AMOUNT_OF_BITCOIN):
            return f"Given the following extracted events stating the entity's total bitcoin holdings: \n\n {filtered_events} \
                \n\n Your job is to pick out the event that is most accurate and relevant \
                    for building the structured output and then transform it into the desired structured data."
        else:
            return None

    async def transform_bitcoin_purchase_events(
        self, events: List[BitcoinEvent]
    ) -> Optional[BitcoinTreasuryUpdate]:
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
                        "content": self.get_user_prompt(events, BitcoinEventType.DEFINITIVE_BITCOIN_ACQUISITION),
                    },
                ],
                response_format=BitcoinTreasuryUpdate,
            )

            # Extract the structured output from the response
            result = chat_completion.choices[0].message.parsed
            return result

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
            return None
        
    async def transform_bitcoin_total_holdings_events(
        self, events: List[BitcoinEvent]
    ) -> Optional[TotalBitcoinHoldings]:
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
                        "content": self.get_user_prompt(events, BitcoinEventType.DISCLOSURE_OF_TOTAL_AMOUNT_OF_BITCOIN),
                    },
                ],
                response_format=TotalBitcoinHoldings,
            )

            # Extract the structured output from the response
            result = chat_completion.choices[0].message.parsed
            return result

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
            return None