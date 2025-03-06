# src/api/models/entities.py
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import date


class EntitySummary(BaseModel):
    """Summary model for entity list endpoint"""

    name: str = Field(..., description="The entity's legal name")
    ticker: str = Field(..., description="Stock ticker symbol")
    cik: str = Field(..., description="SEC Central Index Key")
    bitcoin_entity_tags: List[str] = Field(
        default_factory=list, description="Bitcoin-related entity classifications"
    )
    bitcoin_holdings: float = Field(default=0.0, description="Total BTC holdings")
    has_official_holdings: bool = Field(
        default=False,
        description="Has XBRL-verified holdings (Holdings disclosed in 10-Q XBRL filings)",
    )


class BitcoinHolding(BaseModel):
    """Model for a Bitcoin holding record"""

    amount: float = Field(..., description="Amount held")
    unit: str = Field(..., description="Unit of measurement (BTC or USD)")
    date_of_disclosure: Optional[str] = Field(
        None, description="Date of the Bitcoin holdings disclosure"
    )
    filing_url: str = Field(..., description="URL to the SEC filing")
    file_date: str = Field(..., description="Filing date")
    source: Literal["Official", "AI"] = Field(
        ..., description="Source of the data (Official/GenAI)"
    )
    confidence_score: Optional[float] = Field(
        None, description="AI confidence score if applicable"
    )


class TreasuryUpdate(BaseModel):
    """Model for Bitcoin treasury updates (purchases/sales)"""

    amount: float = Field(..., description="Amount of Bitcoin")
    update_type: str = Field(..., description="Type of update (Purchase/Sale)")
    unit: str = Field(..., description="Unit of measurement (BTC or USD)")
    date: Optional[str] = Field(None, description="Date of transaction")
    filing_url: str = Field(..., description="URL to the SEC filing")
    file_date: str = Field(..., description="Filing date")
    confidence_score: float = Field(..., description="AI confidence score")


class EntityDetail(BaseModel):
    """Detailed entity model for single entity endpoint"""

    name: str = Field(..., description="The entity's legal name")
    ticker: str = Field(..., description="Stock ticker symbol")
    cik: str = Field(..., description="SEC Central Index Key")
    entity_type: Optional[str] = Field(None, description="Type of entity")
    sic: Optional[str] = Field(
        None, description="Standard Industrial Classification code"
    )
    sic_description: Optional[str] = Field(None, description="Description of SIC code")
    website: Optional[str] = Field(None, description="Entity website")
    bitcoin_entity_tags: List[str] = Field(
        default_factory=list, description="Bitcoin-related classifications"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict, description="Summary statistics"
    )
    holdings: List[BitcoinHolding] = Field(
        default_factory=list, description="Bitcoin holdings records"
    )
    treasury_updates: List[TreasuryUpdate] = Field(
        default_factory=list, description="Bitcoin purchase/sale records"
    )
    filing_count: int = Field(
        default=0, description="Number of Bitcoin-related filings"
    )


class EntityList(BaseModel):
    """Response model for entity list endpoint"""

    count: int = Field(..., description="Total number of entities returned")
    entities: List[EntitySummary] = Field(..., description="List of entity summaries")
