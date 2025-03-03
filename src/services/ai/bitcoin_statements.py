# FILE: src/events.py

from enum import Enum
import logging
from typing import Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from models.util import StatementResults


class BitcoinStatementsExtractor:

    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

    system_prompt = (
        "You are an AI assistant that is used to extract relevant bitcoin statements from SEC filings, "
        "particularly 8-K filings and the Exhibits belonging to 8-K's."
        "Format your response as structured data following the StatementResults schema with a list of BitcoinStatement objects."
    )

    user_prompt = (
        "You are analyzing an SEC 8-K filing to extract structured information about Bitcoin-related statements. "
        "Your task is to identify, classify, and structure Bitcoin-related disclosures within the filing based on the following criteria:\n\n"
        "1. **Extract Bitcoin-related statements**: Identify any sections, paragraphs, or disclosures mentioning "
        "Bitcoin holdings, treasury strategies, financial decisions, or governance updates.\n"
        "2. **Classify the statement type**: Assign the most appropriate `event_type` from the predefined categories:\n"
        "   - BITCOIN_HOLDINGS_DISCLOSURE\n"
        "   - BITCOIN_PURCHASE_ANNOUNCEMENT\n"
        "   - BITCOIN_PURCHASE_EXECUTED\n"
        "   - BITCOIN_SALE\n"
        "   - BITCOIN_TREASURY_POLICY_APPROVAL\n"
        "   - BITCOIN_TREASURY_POLICY_UPDATE\n\n"
        "3. **Distinguishing between Bitcoin purchase types**:\n"
        "   - **BITCOIN_PURCHASE_ANNOUNCEMENT**: When a company announces plans to purchase Bitcoin but does not specify execution details "
        "(e.g., 'Company X intends to buy $1M worth of Bitcoin in the coming months' or 'Company X approved a 1 million $ Bitcoin purchase ).\n"
        "   - **BITCOIN_PURCHASE_EXECUTED**: When a company provides specific details about a completed Bitcoin purchase, including:\n"
        "     - The number of BTC acquired.\n"
        "     - The total purchase cost.\n"
        "     - The average purchase price per BTC.\n"
        "     - The date(s) of the transaction.\n"
        "     - The source of funding (e.g., debt issuance, cash reserves, stock sale).\n\n"
        "4. **Provide a detailed statement description**: Ensure the `statement_description` field provides sufficient "
        "context, accurately summarizing the extracted statement.\n"
        "5. **Assign a confidence score**: This score should be between 0 and 1, reflecting the certainty that the extracted statement is classified correctly.\n"
        "Ensure the extracted information is precise, relevant, and adheres to the specified schema."
    )

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        try:
            self.client = openai_settings.get_async_client()
            self.logger.info("AsyncOpenAI client initialized")
            self.structured_output_model = openai_settings.structured_output_model
            self.logger.info(
                f"Using structured output model: {self.structured_output_model}"
            )

        except Exception as e:
            self.logger.error(f"Error initializing OpenAI API: {e}")

    # FILE: src/services/ai/bitcoin_statements.py

    async def extract_statements(self, raw_text: str) -> Optional[StatementResults]:
        self.logger.info(f"Extracting Bitcoin statements from 8-K filing...")
        self.logger.info(f"Raw text length: {len(raw_text)}")
        try:
            # OpenAI API Call with JSON response format
            chat_completion = await self.client.beta.chat.completions.parse(
                model=self.structured_output_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": self.user_prompt + raw_text[:127500],
                    },
                ],
                response_format=StatementResults,
            )

            # Extract the response content
            response_content = chat_completion.choices[0].message.content
            self.logger.info(f"Raw API response: {response_content}")

            if not response_content:
                self.logger.error("OpenAI response content is empty or None.")
                return None

            # Try to parse the JSON response
            try:
                parsed_response = StatementResults.model_validate_json(response_content)

                # Check if statements are valid
                if not parsed_response.statements:
                    self.logger.error("No statements found in the response.")
                    return None

                self.logger.info(
                    f"Successfully parsed {len(parsed_response.statements)} statements"
                )
                return parsed_response

            except Exception as parse_err:
                self.logger.error(f"Failed to parse response: {parse_err}")
                self.logger.error(f"Response content: {response_content}")
                return None

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
            return None
