from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

from datetime import datetime



# Models for Bitcoin Data

SpotBitcoinETFs = [
    "GBTC",  # Grayscale Bitcoin Trust
    "IBIT",  # iShares Bitcoin Trust (BlackRock)
    "FBTC",  # Fidelity Wise Origin Bitcoin Fund
    "ARKB",  # Ark 21Shares Bitcoin ETF
    "BITB",  # Bitwise Bitcoin ETF
    "HODL",  # VanEck Bitcoin Trust
    "EZBC",  # Franklin Templeton Bitcoin ETF
    "BTC"    # Grayscale Bitcoin Mini Trust
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
    "TAO",   # Grayscale Bittensor Trust
    "SUI",   # Grayscale Sui Trust
    "MKR"    # Grayscale MakerDAO Trust
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
    date: str
    unit: Literal["BTC", "USD"]
    tag: str


class BitcoinFairValueStatement(BaseModel):
    amount: float
    date: str
    unit: Literal["BTC", "USD"]
    tag: str
    

# Models for Bitcoin Events

BitcoinEventType = Literal[
    "DEFINITIVE_BITCOIN_ACQUISITION",
    "DEFINITIVE_BITCOIN_SALE",
    "DISCLOSURE_OF_TOTAL_AMOUNT_OF_BITCOIN",
    "BITCOIN_TREASURY_ANNOUNCEMENT"]

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
    
# Models for Bitcoin Treasury Updates

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