# FILE: src/events.py

import asyncio
import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from modeling.filing.SEC_Filing import SEC_Filing


class CustomDate(BaseModel):
    Year: int
    Month: int
    Day: int


class BitcoinTotalHoldings(BaseModel):

    date: CustomDate = Field(
        description="The date of the bitcoin treasury holdings reporting."
    )

    total_bitcoin_holdings: float = Field(
        description="The total amount of bitcoin in the companies treasury"
    )

    total_net_proceeds_dollars: float = Field(
        description="The total net proceeds in dollars of the bitcoin in the companies treasury"
    )


class BitcoinTotalHoldingsResult(BaseModel):

    confidence_score: float = Field(
        description="The confidence score of the extraction."
    )

    contains_bitcoin_treasury_update: bool = Field(
        description="Whether the filing contains information about a bitcoin treasury update"
    )
    bitcoin_treasury_update: Optional[BitcoinTotalHoldings] = Field(
        description="The bitcoin treasury update event, if applicable."
    )


class BitcoinTreasuryUpdateExtractor:

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

    async def extract_bitcoin_treasury_update(
        self, filing: SEC_Filing
    ) -> Optional[BitcoinTotalHoldingsResult]:
        try:
            chat_completion = await self.client.beta.chat.completions.parse(
                model=self.structured_output_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI financial analyst that is used to extract the new total Bitcoin holdings in the companies treasury",
                    },
                    {
                        "role": "user",
                        "content": "Can you extract the total bitcoin holdings of the company and the total net proceeds in dollars from the following filing html content : \n\n"
                        + filing.content_html_str,
                    },
                ],
                response_format=BitcoinTotalHoldingsResult,
            )

            # Extract the structured output from the response
            result = chat_completion.choices[0].message.parsed

            return result

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")

    async def extract_bitcoin_treasury_updates(
        self, filings: List[SEC_Filing]
    ) -> List[Optional[BitcoinTotalHoldingsResult]]:
        tasks = [self.extract_bitcoin_treasury_update(filing) for filing in filings]
        return await asyncio.gather(*tasks)
