# FILE: src/events.py

import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from modeling.bitcoin_purchase.BitcoinPurchase import BitcoinPurchase
from modeling.filing.SEC_Filing import SEC_Filing


class Step(BaseModel):
    explanation: str = Field(..., description="The explanation of the step.")
    output: str = Field(..., description="The output of the step.")


class FinalTotalBitcoinHoldings(BaseModel):
    total_bitcoin_held: float = Field(
        ..., description="The total amount of bitcoin in the companies treasury"
    )
    total_net_proceeds_dollars: float = Field(
        ...,
        description="The total net proceeds in dollars of the bitcoin in the companies treasury",
    )
    avg_price_per_bitcoin: float = Field(
        description="The average purchase price per bitcoin for the total bitcoin held by the company."
    )


class ChainOfThoughtResponse(BaseModel):
    steps: List[Step] = Field(
        ..., description="The list of steps in the chain of thought."
    )
    final_answer: FinalTotalBitcoinHoldings = Field(
        ..., description="The final answer in the chain of thought."
    )

    confidence_score: float = Field(
        description="The confidence score of the extraction."
    )


class ChainOfThoughtExtractor:

    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

    system_prompt = "You are an AI assistant that is used to reason about the total bitcoins held by a company"
    user_prompt = "Can you extract your reasoning behind how you get to the total bitcoin holdings of a company, given the following SEC filing, sometimes the total bitcoin holdings are contained in a table : \n\n"

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

    async def extract_chain_of_thoughts(
        self, filing: SEC_Filing
    ) -> Optional[ChainOfThoughtResponse]:
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
                        "content": self.user_prompt + filing.content_html_str,
                    },
                ],
                response_format=ChainOfThoughtResponse,
            )

            # Extract the structured output from the response
            result = chat_completion.choices[0].message.parsed
            self.logger.info(f"Structured output: {result}")

            return result

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
