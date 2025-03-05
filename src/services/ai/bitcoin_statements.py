# FILE: src/events.py

from enum import Enum
import logging
from typing import List, Optional
from logging import Logger
from openai import AsyncOpenAI
from config import openai_settings
from models.util import (
    StatementResults,
    StatementType,
    BitcoinHoldingsDisclosure_GEN_AI,
    BitcoinStatement,
    HoldingStatementsResult,
    TreasuryUpdateStatementResult_GEN_AI,
    TreasuryUpdateStatementsResult,
)
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
        "3. **BITCOIN_HOLDINGS_DISCLOSURE**: When the company discloses numerically how much bitcoin they hold in bitcoin units or dollar units. Bitcoin units are preferred.\n"
        "    If no specific amount is disclosed, do not classify the statement as a BITCOIN_HOLDINGS_DISCLOSURE.\n"
        "4. **Distinguishing between Bitcoin purchase types**:\n"
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
        try:
            # OpenAI API Call with JSON response format
            chat_completion = await self.client.beta.chat.completions.parse(
                model=self.structured_output_model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt_general_statements,
                    },
                    {
                        "role": "user",
                        "content": self.user_prompt_general_statements
                        + raw_text[:127500],
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

    async def extract_holding_statements(
        self, bitcoin_statements: List[BitcoinStatement]
    ) -> Optional[HoldingStatementsResult]:
        # Retrieve the Holding disclosure statements
        general_holding_statements = [
            statement
            for statement in bitcoin_statements
            if statement.statement_type == StatementType.BITCOIN_HOLDINGS_DISCLOSURE
            or statement.statement_type == StatementType.BITCOIN_PURCHASE_EXECUTED
        ]
        # Prompts for AI request
        system_prompt = "You are an AI assistant that is used to extract structured output from statements, extracted out of SEC filings (8-K)."
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
            "- When the type of the BitcoinStatement is `BITCOIN_PURCHASE_EXECUTED`, avoid disclosing holdings of the individual purchase, such as 'the Company completed a purchase of 213.43 bitcoin'.\n"
            "- Avoid returning disclosures where the amount is not explicitly mentioned and filling in the amount to 0 \n"
            "- Focus only on statements that disclose **specific holdings** of Bitcoin.\n"
            "- If multiple amounts or dates are mentioned, choose the **most relevant** one based on the context.\n"
            "- If a statement does not provide a clear disclosure of Bitcoin holdings, exclude it from the output.\n\n"
            "### Response Format:\n"
            "Your response should be a **structured JSON list** of `BitcoinHoldingsDisclosure_GEN_AI` objects, where each object follows this format:\n\n"
            "[\n"
            "  {\n"
            '    "amount": 100.5,\n'
            '    "unit": "BTC",\n'
            '    "rdate": "2024-02-15",\n'
            '    "confidence_score": 0.95\n'
            "  },\n"
            "  {\n"
            '    "amount": 5000000,\n'
            '    "unit": "USD",\n'
            '    "rdate": "2023-12-01",\n'
            '    "confidence_score": 0.88\n'
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

    async def extract_treasury_updates(
        self, bitcoin_statements: List[BitcoinStatement]
    ) -> Optional[TreasuryUpdateStatementsResult]:
        # Retrieve the treasury update statements
        treasury_update_statements = [
            statement
            for statement in bitcoin_statements
            if statement.statement_type == StatementType.BITCOIN_PURCHASE_ANNOUNCEMENT
            or statement.statement_type == StatementType.BITCOIN_PURCHASE_EXECUTED
            or statement.statement_type == StatementType.BITCOIN_SALE
        ]

        # Skip if no relevant statements
        if not treasury_update_statements:
            self.logger.info("No treasury update statements found.")
            return None

        # Prompts for AI request
        system_prompt = "You are an AI assistant that is used to extract structured output from statements extracted from SEC filings (8-K)."
        user_prompt = (
            "You will receive a list of bitcoin statements, each represented as an instance of the `BitcoinStatement` class, which includes:\n"
            "- `statement_type`: The type of bitcoin statement.\n"
            "- `statement_description`: A detailed textual description of the statement.\n"
            "- `confidence_score`: The confidence level of the extracted statement.\n\n"
            "Your task is to extract **bitcoin treasury updates** from these statements and return them as a list of `TreasuryUpdateDisclosure_GEN_AI` objects. Each extracted update should contain:\n\n"
            "1. **amount**: The amount of bitcoin involved in the update.\n"
            "   - Preferably extracted in **BTC**.\n"
            "   - If BTC is not available, extract the amount in **USD**.\n\n"
            "2. **update_type**: The type of treasury update.\n"
            "   - Must be either **'Purchase'** or **'Sale'**.\n\n"
            "3. **unit**: The unit of measurement of the amount.\n"
            "   - Must be either **'BTC'** or **'USD'**.\n\n"
            "4. **date** (optional): The date of the purchase or sale.\n"
            "   - If a date is present in the statement, extract it.\n"
            "   - Format the date as **YYYY-MM-DD**.\n\n"
            "5. **confidence_score**: The confidence level of the extracted treasury update.\n"
            "   - Based on the extraction you are performing now and not the confidence_score of the given BitcoinStatements.\n\n"
            "### Guidelines for Extraction:\n"
            "- AVOID quarterly or annual treasury updates such as : 'The fourth quarter of 2024 marked our largest ever increase in quarterly bitcoin holdings, culminating in the acquisition of 218,887 bitcoins acquired for $20.5 billion, since the end of Q3.'"
            "- Focus on **completed transactions** for BITCOIN_PURCHASE_EXECUTED statements.\n"
            "- For BITCOIN_PURCHASE_ANNOUNCEMENT statements, extract details of the announced purchase.\n"
            "- Look for explicit amounts, prices, and dates in the statements.\n"
            "- If a statement mentions both a BTC amount and a USD amount, prioritize the BTC amount.\n"
            "- If multiple purchases/sales are mentioned in one statement, extract the most clearly defined one.\n"
            "- Don't extract general treasury policy updates that don't involve specific purchases/sales.\n\n"
            "### Response Format:\n"
            "Your response should be a **structured JSON list** of `TreasuryUpdateDisclosure_GEN_AI` objects, where each object follows this format:\n\n"
            "[\n"
            "  {\n"
            '    "amount": 100.5,\n'
            '    "update_type": "Purchase",\n'
            '    "unit": "BTC",\n'
            '    "date": "2024-02-15",\n'
            '    "confidence_score": 0.95\n'
            "  },\n"
            "  {\n"
            '    "amount": 5000000,\n'
            '    "update_type": "Sale",\n'
            '    "unit": "USD",\n'
            '    "date": "2023-12-01",\n'
            '    "confidence_score": 0.88\n'
            "  }\n"
            "]\n\n"
            "Ensure that all extracted data is as accurate as possible while maintaining the highest confidence in the updates. "
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
                        "content": user_prompt + str(treasury_update_statements),
                    },
                ],
                response_format=TreasuryUpdateStatementsResult,
            )

            # Extract the response content
            response_content = chat_completion.choices[0].message.parsed
            if response_content:
                self.logger.info(
                    "GenAI Bitcoin Treasury Updates extracted successfully."
                )
                return response_content
            if not response_content:
                self.logger.error("OpenAI response content is empty or None.")
                return None

        except Exception as e:
            self.logger.error(f"Error extracting treasury updates: {e}")
            return None
