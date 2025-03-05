from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator
from models.filing.Bitcoin_Filing import Bitcoin_Filing

from datetime import datetime


# Models for official 10-Q XBRL extractions

SpotBitcoinETFs = [
    "GBTC",  # Grayscale Bitcoin Trust
    "IBIT",  # iShares Bitcoin Trust (BlackRock)
    "FBTC",  # Fidelity Wise Origin Bitcoin Fund
    "ARKB",  # Ark 21Shares Bitcoin ETF
    "BITB",  # Bitwise Bitcoin ETF
    "HODL",  # VanEck Bitcoin Trust
    "EZBC",  # Franklin Templeton Bitcoin ETF
    "BTC",  # Grayscale Bitcoin Mini Trust
]

GrayscaleTrusts = [
    "GBTC",  # Grayscale Bitcoin Trust
    "ETHE",  # Grayscale Ethereum Trust
    "ETCG",  # Grayscale Ethereum Classic Trust
    "LTCN",  # Grayscale Litecoin Trust
    "BCHG",  # Grayscale Bitcoin Cash Trust
    "GXLM",  # Grayscale Stellar Lumens Trust
    "ZCSH",  # Grayscale Zcash Trust
    "HZEN",  # Grayscale Horizen Trust
    "MANA",  # Grayscale Decentraland Trust
    "GLNK",  # Grayscale Chainlink Trust
    "GBAT",  # Grayscale Basic Attention Token Trust
    "GSOL",  # Grayscale Solana Trust
    "FILG",  # Grayscale Filecoin Trust
    "GLIV",  # Grayscale Livepeer Trust
    "DEFG",  # Grayscale Decentralized Finance (DeFi) Fund
    "GDLC",  # Grayscale Digital Large Cap Fund
    "TAO",  # Grayscale Bittensor Trust
    "SUI",  # Grayscale Sui Trust
    "MKR",  # Grayscale MakerDAO Trust
]


class BitcoinEntityTag(str, Enum):
    MINER = "miner"
    SPOT_BITCOIN_ETF = "spot_bitcoin_etf"
    CRYPTO_FUND = "crypto_fund"
    GRAYSCALE_TRUST = "grayscale_trust"
    CRYPTO_SERVICE_PROVIDER = "crypto_service_provider"
    ACTIVE_BTC_STRATEGY = "active_btc_strategy"
    ANNOUNCED_BTC_STRATEGY = "announced_btc_strategy"
    MENTIONED_BTC_IN_FILING = "mentioned_btc_in_filing"


class BitcoinHoldingsStatement(BaseModel):
    amount: float
    report_date: str
    unit: Literal["BTC", "USD"]
    tag: str


class HoldingStatementTenQ(BaseModel):

    statement: BitcoinHoldingsStatement
    filing: Bitcoin_Filing


class BitcoinFairValueStatement(BaseModel):
    amount: float = Field(default=0)
    report_date: str
    unit: Literal["BTC", "USD"]
    tag: str


class FairValueStatementTenQ(BaseModel):

    statement: BitcoinFairValueStatement
    filing: Bitcoin_Filing


# Models For GenAI Bitcoin Events


class BitcoinHoldingsDisclosure_GEN_AI(BaseModel):
    amount: float = Field(
        description="The amount of bitcoin disclosed in the filing. The unit of this amount is preferred to be in BTC, if this is not available USD is also acceptable."
    )
    unit: Literal["BTC", "USD"] = Field(
        description="The unit of the amount of bitcoin disclosed in the filing."
    )
    date: Optional[str] = Field(
        description="The date belonging to the bitcoin holdings disclosure.  \
            This date should be in the format YYYY-MM-DD."
    )
    confidence_score: float = Field(
        ..., description="The confidence score of the bitcoin holdings disclosure."
    )

    @model_validator(mode="before")
    def check_confidence_score(cls, values):
        confidence_score = values.get("confidence_score")
        if confidence_score is not None and (
            confidence_score < 0 or confidence_score > 1
        ):
            raise ValueError("Confidence score must be between 0 and 1.")
        return values


class TreasuryUpdateDisclosure_GEN_AI(BaseModel):
    amount: float = Field(
        description="The amount of bitcoin disclosed in the filing. The unit of this amount is preferred to be in BTC, if this is not available USD is also acceptable."
    )

    update_type: Literal["Purchase", "Sale"] = Field(
        description="The type of the bitcoin treasury update: a purchase or sale of bitcoin"
    )

    unit: Literal["BTC", "USD"] = Field(
        description="The unit of the amount of the treasury update disclosed in the filing."
    )

    date: Optional[str] = Field(
        description="The date belonging to the purchase or sale .  \
            This date should be in the format YYYY-MM-DD."
    )
    confidence_score: float = Field(
        ..., description="The confidence score of the bitcoin holdings disclosure."
    )

    @model_validator(mode="before")
    def check_confidence_score(cls, values):
        confidence_score = values.get("confidence_score")
        if confidence_score is not None and (
            confidence_score < 0 or confidence_score > 1
        ):
            raise ValueError("Confidence score must be between 0 and 1.")
        return values


# File: models/util.py


class StatementType(str, Enum):
    # Bitcoin treasury events
    BITCOIN_HOLDINGS_DISCLOSURE = "BITCOIN_HOLDINGS_DISCLOSURE"  # No periods
    BITCOIN_PURCHASE_ANNOUNCEMENT = "BITCOIN_PURCHASE_ANNOUNCEMENT"
    BITCOIN_PURCHASE_EXECUTED = "BITCOIN_PURCHASE_EXECUTED"
    BITCOIN_SALE = "BITCOIN_SALE"

    # Bitcoin treasury approvals
    BITCOIN_TREASURY_POLICY_APPROVAL = "BITCOIN_TREASURY_POLICY_APPROVAL"
    BITCOIN_YIELD_STATEMENT = "BITCOIN_YIELD_STATEMENT"


class BitcoinStatement(BaseModel):
    statement_type: StatementType = Field(
        ..., description="The type of bitcoin statement."
    )
    statement_description: str = Field(
        ..., description="A detailed description of the statement."
    )
    confidence_score: float = Field(
        ..., description="The confidence score of the statement extraction."
    )

    @model_validator(mode="before")
    def check_confidence_score(cls, values):
        confidence_score = values.get("confidence_score")
        if confidence_score is not None and (
            confidence_score < 0 or confidence_score > 1
        ):
            raise ValueError("Confidence score must be between 0 and 1.")
        return values


class StatementResults(BaseModel):
    statements: List[BitcoinStatement] = Field(
        ...,
        description="The list of extracted statements, related to bitcoin, in the SEC Filing",
    )


class HoldingStatementsResult(BaseModel):
    holding_statements: List[BitcoinHoldingsDisclosure_GEN_AI] = Field(
        ..., description="The list of extracted bitcoin holdings disclosures."
    )


class TreasuryUpdateStatementsResult(BaseModel):
    treasury_update_statements: List[TreasuryUpdateDisclosure_GEN_AI] = Field(
        ..., description="The list of extracted bitcoin treasury updates."
    )


class StatementResult_GEN_AI(BaseModel):
    statements: List[BitcoinStatement] = Field(default=[])
    filing: Bitcoin_Filing


class HoldingStatementResult_GEN_AI(BaseModel):
    statements: List[BitcoinHoldingsDisclosure_GEN_AI] = Field(default=[])
    filing: Bitcoin_Filing


class TreasuryUpdateStatementResult_GEN_AI(BaseModel):
    statements: List[TreasuryUpdateDisclosure_GEN_AI] = Field(default=[])
    filing: Bitcoin_Filing
