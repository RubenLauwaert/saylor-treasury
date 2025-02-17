import asyncio
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
    extracted_btc_events: List[BitcoinEvent] = Field(default=[])
    # Bools
    has_extracted_events: bool = Field(default=False)

    @classmethod
    def from_query_hit(cls, hit: QueryHit) -> "Bitcoin_Filing":
        logger = logging.getLogger(cls.__name__)
        # Optional fields
        return cls(
            url=hit.url,
            accession_number=hit.accession_number,
            file_type=hit.file_type,
            form_type=hit.form_type,
            file_date=hit.file_date,
        )
        
    @staticmethod
    async def extract_bitcoin_events_for(bitcoin_filings: List["Bitcoin_Filing"]) -> List["Bitcoin_Filing"]:
        batch_size = 10  # Number of requests per batch
        delay = 1  # Delay in seconds between batches
        event_extractor = EventsExtractor()
        for i in range(0, len(bitcoin_filings), batch_size):
            batch = bitcoin_filings[i:i + batch_size]
            await asyncio.gather(*(filing.extract_bitcoin_events(event_extractor) for filing in batch))
            if i + batch_size < len(bitcoin_filings):
                await asyncio.sleep(delay)  # Wait for 1 second between batches

        return bitcoin_filings
        
    async def get_html_content(self) -> str:
        logger = logging.getLogger(self.__class__.__name__)
        html_content = None
        try:
            html_content = await SEC_Filing.get_raw_content_html(self.url)
        except Exception as e:
            logger.error(f"Failed to load html content for filing {self.url}: {e}")
        return html_content
    
    async def extract_bitcoin_events(self, extractor: EventsExtractor) -> "Bitcoin_Filing":
        logger = logging.getLogger(self.__class__.__name__)
        try:
                raw_content_html = await self.get_html_content()
                extracted_events = await extractor.extract_events(raw_content_html)
                self.extracted_btc_events = extracted_events.events
                self.has_extracted_events = True
                logger.info(f"Extracted bitcoin events from filing {self.url}")
        except Exception as e:
            logger.error(f"Failed to extract bitcoin events from filing {self.url}: {e}")
        return self
    
    
        
    
