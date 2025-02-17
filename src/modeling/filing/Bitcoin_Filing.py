from pydantic import BaseModel, Field
from typing import Optional, List, Literal

from modeling.filing.SEC_Filing import SEC_Filing
from services.ai.bitcoin_events import *
from modeling.sec_edgar.efts.query import QueryHit


class BitcoinTreasuryUpdate(BaseModel):
    type: Literal["Acquisition", "Sale"]
    update_date: str = Field(
        ...,
        description="The date of the bitcoin treasury update in isoformat YYYY-MM-DD",
    )
    bitcoin_amount: float = Field(description="The amount of bitcoin acquired or sold")
    average_price_per_bitcoin: float = Field(
        description="The average price per bitcoin for the bitcoin acquisition or sale"
    )


class TotalBitcoinHoldings(BaseModel):
    total_bitcoin_holdings: float = Field(
        ..., description="The total amount of bitcoin held by the entity"
    )
    average_price_per_bitcoin: float = Field(
        description="The average price per bitcoin for the total bitcoin holdings"
    )


class Bitcoin_Filing(BaseModel):

    # Necessary data
    url: str
    accession_number: str
    file_type: str
    root_form_type: str
    file_date: str

    # Bools
    contains_raw_content: bool = Field(default=False)
    contains_parsed_content: bool = Field(default=False)
    contains_btc_events: bool = Field(default=False)
    has_btc_update: bool = Field(default=False)
    has_total_btc_holdings: bool = Field(default=False)
    # Optional Data
    raw_content_html: Optional[str]
    parsed_content: Optional[str]
    extracted_btc_events: Optional[BitcoinFilingEventsResult]
    btc_treasury_update: Optional[BitcoinTreasuryUpdate]
    btc_total_holdings: Optional[TotalBitcoinHoldings]

    @classmethod
    async def from_query_hit(
        cls, query_hit: QueryHit, sec_filing: SEC_Filing
    ) -> "Bitcoin_Filing":
        logger = logging.getLogger(cls.__name__)

        contains_raw_content = sec_filing.has_content
        raw_content_html = sec_filing.content_html_str
        contains_bitcoin_events = False
        bitcoin_events = None

        # Extract bitcoin events
        try:
            events_extractor = EventsExtractor()
            bitcoin_events = await events_extractor.extract_events_from_filing(
                sec_filing
            )

            contains_bitcoin_events = len(bitcoin_events.events) > 0

        except Exception as e:
            logger.error(f"Error extracting bitcoin events: {e}")
