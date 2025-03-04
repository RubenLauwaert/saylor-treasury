# FILE: src/events.py

from enum import Enum
import logging
from typing import List, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from models.util import StatementResults, StatementType, BitcoinHoldingsDisclosure_GEN_AI, BitcoinStatement, HoldingStatementsResult
from models.filing.Bitcoin_Filing import Bitcoin_Filing


class BitcoinStatementsExtractor:

    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

    system_prompt_general_statements = (
        "You are an AI assistant that is used to extract relevant bitcoin statements from SEC filings, "
        "particularly 8-K filings and the Exhibits belonging to 8-K's."
        "Format your response as structured data following the StatementResults schema with a list of BitcoinStatement objects."
    )

    user_prompt_general_statements = (
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

    async def extract_statements(
        self, raw_text: str
    ) -> Optional[StatementResults]:
        self.logger.info(f"Extracting Bitcoin statements from 8-K filing...")
        try:
            # OpenAI API Call with JSON response format
            chat_completion = await self.client.beta.chat.completions.parse(
                model=self.structured_output_model,
                messages=[
                    {"role": "system", "content": self.system_prompt_general_statements},
                    {
                        "role": "user",
                        "content": self.user_prompt_general_statements + raw_text[:127500],
                    },
                ],
                response_format=StatementResults,
            )
            # Extract the response content
            response_content = chat_completion.choices[0].message.parsed
            if response_content:
                self.logger.info("Bitcoin statements extracted successfully.")
                return response_content
            if not response_content:
                self.logger.error("OpenAI response content is empty or None.")
                return None

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
            return None
        
    async def extract_holding_statements(self, bitcoin_statements: List[BitcoinStatement]) -> Optional[HoldingStatementsResult]:
        # Retrieve the Holding disclosure statements
        general_holding_statements = [
            statement for statement in bitcoin_statements
            if statement.statement_type == StatementType.BITCOIN_HOLDINGS_DISCLOSURE
        ]
        # Prompts for AI request
        system_prompt = ( "You are an AI assistant that is used to extract structured output from statements, extracted out of SEC filings (8-K).")
        user_prompt = (
        "You will receive a list of bitcoin statements, each represented as an instance of the `BitcoinStatement` class, which includes:\n"
        "- `statement_type`: The type of bitcoin statement.\n"
        "- `statement_description`: A detailed textual description of the statement.\n"
        "- `confidence_score`: The confidence level of the extracted statement.\n\n"
        "Your task is to extract **bitcoin holdings disclosures** from these statements and return them as a list of `BitcoinHoldingsDisclosure_GEN_AI` objects. Each extracted disclosure should contain:\n\n"
        "1. **amount**: The disclosed amount of bitcoin holdings.\n"
        "   - Preferably extracted in **BTC**.\n"
        "   - If BTC is not available, extract the amount in **USD**.\n\n"
        "2. **unit**: The unit of measurement of the disclosed amount.\n"
        "   - Must be either **'BTC'** or **'USD'**.\n\n"
        "3. **date** (optional): The date related to the bitcoin holdings disclosure.\n"
        "   - If a date is present in the statement, extract it.\n"
        "   - Format the date as **YYYY-MM-DD**.\n\n"
        "4. **confidence_score**: The confidence level of the extracted disclosure.\n"
        "   - Based on the extraction you are performing now and not the confidence_score of the given BitcoinStatements.\n\n"
        "### Guidelines for Extraction:\n"
        "- Focus only on statements that disclose **specific holdings** of Bitcoin.\n"
        "- If multiple amounts or dates are mentioned, choose the **most relevant** one based on the context.\n"
        "- If a statement does not provide a clear disclosure of Bitcoin holdings, exclude it from the output.\n\n"
        "### Response Format:\n"
        "Your response should be a **structured JSON list** of `BitcoinHoldingsDisclosure_GEN_AI` objects, where each object follows this format:\n\n"
        "[\n"
        "  {\n"
        "    \"amount\": 100.5,\n"
        "    \"unit\": \"BTC\",\n"
        "    \"rdate\": \"2024-02-15\",\n"
        "    \"confidence_score\": 0.95\n"
        "  },\n"
        "  {\n"
        "    \"amount\": 5000000,\n"
        "    \"unit\": \"USD\",\n"
        "    \"rdate\": \"2023-12-01\",\n"
        "    \"confidence_score\": 0.88\n"
        "  }\n"
        "]\n\n"
        "Ensure that all extracted data is as accurate as possible while maintaining the highest confidence in the disclosures."
        "Here is the list of BitcoinStatements, extracted from the 8-K filing: \n\n"
        )
        
        try:
            # OpenAI API Call with JSON response format
            chat_completion = await self.client.beta.chat.completions.parse(
                model=self.structured_output_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": user_prompt + str(general_holding_statements),
                    },
                ],
                response_format=HoldingStatementsResult,
            )
            # Extract the response content
            response_content = chat_completion.choices[0].message.parsed
            if response_content:
                self.logger.info("GenAI Bitcoin Holdings extracted successfully.")
                return response_content
            if not response_content:
                self.logger.error("OpenAI response content is empty or None.")
                return None

        except Exception as e:
            self.logger.error(f"Error extracting events: {e}")
            return None
        
    
