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
    form_type: str
    file_date: str
    # Optional data
    raw_content_html: Optional[str]
    extracted_btc_events: Optional[BitcoinFilingEventsResult]

    # Bools
    contains_raw_content: bool = Field(default=False)
    has_extracted_events: bool = Field(default=False)

    @classmethod
    async def from_query_hit(cls, hit: QueryHit) -> "Bitcoin_Filing":
        logger = logging.getLogger(cls.__name__)
        # Optional fields
        raw_content_html = None
        extracted_btc_events = None
        # Bools
        contains_raw_content = False
        has_extracted_events = False

        try:
            raw_content_html = await SEC_Filing.get_raw_content_html(hit.url)
            contains_raw_content = True
            # Extract events
            extracted_btc_events = await EventsExtractor().extract_events(
                raw_content_html
            )
            has_extracted_events = True

        except Exception as e:
            logger.error(f"Error extracting bitcoin events from filing: {e}")

        return cls(
            url=hit.url,
            accession_number=hit.accession_number,
            file_type=hit.file_type,
            form_type=hit.form_type,
            file_date=hit.file_date,
            raw_content_html=raw_content_html,
            extracted_btc_events=extracted_btc_events,
            contains_raw_content=contains_raw_content,
            has_extracted_events=has_extracted_events,
        )
