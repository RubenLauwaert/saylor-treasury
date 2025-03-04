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
    holding_statements: List[BitcoinHoldingsDisclosure_GEN_AI] = Field(..., description="The list of extracted bitcoin holdings disclosures.")


class StatementResult_GEN_AI(BaseModel):
    statements: List[BitcoinStatement] = Field(default=[])
    filing: Bitcoin_Filing
    
class HoldingStatementResult_GEN_AI(BaseModel):
    statements: List[BitcoinHoldingsDisclosure_GEN_AI] = Field(default=[])
    filing: Bitcoin_Filing


# Models for Bitcoin Treasury Updates


class BitcoinTreasuryUpdate(BaseModel):
    type: Literal["Purchase", "Sale"]

    bitcoin_amount: Optional[float] = Field(
        None,
        description="The amount of bitcoin acquired or sold. If this value is not explicitly stated in the input but inferred or calculated, set 'bitcoin_amount_filled_in' to True.",
    )
    average_price_per_bitcoin: Optional[int] = Field(
        None,
        description="The average price per bitcoin for the acquisition or sale. If this value is not explicitly stated in the input but inferred or calculated, set 'average_price_per_bitcoin_filled_in' to True.",
    )
    amount_in_usd: Optional[int] = Field(
        None,
        description="The total amount in USD spent or received for the acquisition or sale. If this value is not explicitly stated in the input but inferred or calculated, set 'amount_in_usd_filled_in' to True.",
    )

    @model_validator(mode="before")
    def check_either_bitcoin_amount_or_amount_in_usd(cls, values):
        bitcoin_amount = values.get("bitcoin_amount")
        amount_in_usd = values.get("amount_in_usd")
        average_price_per_bitcoin = values.get("average_price_per_bitcoin")

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
        ...,
        description="The total amount of dollars spent for the total bitcoin holdings",
    )

    @model_validator(mode="before")
    def check_fields(cls, values):
        total_bitcoin_holdings = values.get("total_bitcoin_holdings")
        average_price_per_bitcoin = values.get("average_price_per_bitcoin")
        total_amount_in_usd = values.get("total_amount_in_usd")

        if total_bitcoin_holdings is None:
            raise ValueError(
                "The total amount of bitcoin held by the entity must be provided."
            )

        return values


# Models for GenAI bitcoin holdings and treasury updates


class GenAI_BitcoinTreasuryUpdateStatement(BaseModel):
    # Data about the bitcoin treasury update
    bitcoin_treasury_update: BitcoinTreasuryUpdate

    # Data about the filing where the statement was found
    filing_url: str
    file_date: str
    accession_number: str
    form_type: str
    file_type: str

    # @classmethod
    # def from_bitcoin_filing(cls, filing: Bitcoin_Filing) -> "GenAI_BitcoinTreasuryUpdateStatement":

    #     return cls(bitcoin_treasury_update=filing.bitcoin_treasury_update,
    #                filing_url=filing.url,
    #                file_date=filing.file_date,
    #                accession_number=filing.accession_number,
    #                form_type=filing.form_type,
    #                file_type=filing.file_type)


class GenAI_BitcoinHoldingsStatement(BaseModel):
    # Data about the bitcoin holdings
    bitcoin_data: TotalBitcoinHoldings

    # Data about the filing where the statement was found
    filing_url: str
    file_date: str
    accession_number: str
    form_type: str
    file_type: str

    # @classmethod
    # def from_bitcoin_filing(cls, filing: Bitcoin_Filing) -> "GenAI_BitcoinHoldingsStatement":
    #     return cls(bitcoin_data=filing.total_bitcoin_holdings,
    #                filing_url=filing.url,
    #                file_date=filing.file_date,
    #                accession_number=filing.accession_number,
    #                form_type=filing.form_type,
    #                file_type=filing.file_type)
