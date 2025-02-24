import asyncio
from pydantic import BaseModel, Field
from typing import Optional, List, Literal

from modeling.filing.SEC_Filing import SEC_Filing
from services.ai.bitcoin_events import *
from services.ai.events_transformer import *
from modeling.sec_edgar.efts.query import QueryHit
from modeling.parsers.generic.Filing_Parser_Generic import Filing_Parser_Generic


from config import openai_settings as ai_settings





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
    has_raw_content: bool = Field(default=False)
    has_bitcoin_treasury_update: bool = Field(default=False)
    has_total_bitcoin_holdings: bool = Field(default=False)
    
    # Raw content
    raw_text: str = Field(default="")
    # Bitcoin Treasury data
    bitcoin_treasury_update: Optional[BitcoinTreasuryUpdate] = Field(
        default=None,
        description="The Bitcoin Treasury Update data for the entity."
    )
    total_bitcoin_holdings: Optional[TotalBitcoinHoldings] = Field(
        default=None,
        description="The Total Bitcoin Holdings data for the entity."
    )
    
    # Getters
    def get_bitcoin_acquisition_events(self) -> List[BitcoinEvent]:
        acquisition_events = [
            event for event in self.extracted_btc_events if event.event_type == BitcoinEventType.DEFINITIVE_BITCOIN_ACQUISITION
        ]
        return acquisition_events
    
    def get_bitcoin_sale_events(self) -> List[BitcoinEvent]:
        sale_events = [
            event for event in self.extracted_btc_events if event.event_type == BitcoinEventType.DEFINITIVE_BITCOIN_SALE
        ]
        return sale_events
    
    def get_bitcoin_total_holdings_events(self) -> List[BitcoinEvent]:
        total_holdings_events = [
            event for event in self.extracted_btc_events if event.event_type == BitcoinEventType.DISCLOSURE_OF_TOTAL_AMOUNT_OF_BITCOIN
        ]
        return total_holdings_events
    
    
    
    
    # Constructor

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
        
    # Async methods    
    
    async def load_html_content(self) -> "Bitcoin_Filing":
        logger = logging.getLogger(self.__class__.__name__)
        has_raw_content = False
        raw_content_html = ""
        try:
            # Retrieve raw html content
            html_content = await SEC_Filing.get_raw_content_html(self.url)
            # Get raw text out of html 
            raw_text = Filing_Parser_Generic.get_cleaned_text(html_content)
            self.raw_text = raw_text
            self.has_raw_content = True
        except Exception as e:
            logger.error(f"Failed to load html content for filing {self.url}: {e}")
        return self
        
    
    
    async def extract_bitcoin_events(self, extractor: EventsExtractor) -> "Bitcoin_Filing":
        logger = logging.getLogger(self.__class__.__name__)
        try:    
            if self.has_raw_content and len(self.raw_text) > 0:
                extracted_events = await extractor.extract_events(self.raw_text)
                self.extracted_btc_events = extracted_events.events
                self.has_extracted_events = True
                logger.info(f"Extracted bitcoin events from filing {self.url}")
            else:
                raise ValueError("No raw content available")
                
        except Exception as e:
            logger.error(f"Failed to extract bitcoin events from filing {self.url}: {e}")
        return self
    
    
    async def parse_bitcoin_events(self, transformer: EventsTransformer) -> "Bitcoin_Filing":
        logger = logging.getLogger(self.__class__.__name__)
        
        try:
            # Try to transform events to bitcoin total holdings
                total_holdings_events = self.get_bitcoin_total_holdings_events()
                if len(total_holdings_events) > 0:
                    parsed_btc_holdings = await transformer.transform_bitcoin_total_holdings_events(total_holdings_events)
                    if parsed_btc_holdings is not None:
                        self.total_bitcoin_holdings = parsed_btc_holdings
                        self.has_total_bitcoin_holdings = True
                        logger.info(f"Transformed total bitcoin holdings for filing {self.url}")
                #Try to transform events to bitcoin treasury update
                acquisition_events = self.get_bitcoin_acquisition_events()
                if len(acquisition_events) > 0:
                    parsed_treasury_update = await transformer.transform_bitcoin_purchase_events(acquisition_events)
                    if parsed_treasury_update is not None:
                        self.bitcoin_treasury_update = parsed_treasury_update
                        self.has_bitcoin_treasury_update = True
                        logger.info(f"Transformed bitcoin purchases for filing {self.url}")
        except Exception as e:
            logger.error(f"Failed to transform bitcoin events for filing {self.url}: {e}")
    
    
    @staticmethod
    async def load_html_content_for(bitcoin_filings: List["Bitcoin_Filing"]) -> List["Bitcoin_Filing"]:
        batch_size = 10  # Number of requests per batch
        delay = 1.1  # Delay in seconds between batches
        for i in range(0, len(bitcoin_filings), batch_size):
            batch = bitcoin_filings[i:i + batch_size]
            await asyncio.gather(*(filing.load_html_content() for filing in batch))
            if i + batch_size < len(bitcoin_filings):
                await asyncio.sleep(delay)  # Wait for 1 second between batches

        return bitcoin_filings
    
    @staticmethod
    async def extract_bitcoin_events_for(bitcoin_filings: List["Bitcoin_Filing"]) -> List["Bitcoin_Filing"]:
        rpm = ai_settings.requests_per_minute
        tpm = ai_settings.tokens_per_minute
        chars_per_min = tpm * 3 # Conservatively assume 3 characters per token
        tokens_per_request = ai_settings.tokens_per_request
        event_extractor = EventsExtractor()
        sum_chars = sum([len(filing.raw_text) for filing in bitcoin_filings])
        logging.info(f"Sum of chars: {sum_chars}")
        batch_size = len(bitcoin_filings)
        # If sum chars is less then chars_per_min then we can process all filings in one batch
        if sum_chars < chars_per_min and len(bitcoin_filings) < rpm:
            await asyncio.gather(*(filing.extract_bitcoin_events(event_extractor) for filing in bitcoin_filings))
            return bitcoin_filings
        else:
            batch_size = min(rpm, int(tpm / tokens_per_request))  # Number of requests per batch
            delay = 60  # Delay in seconds between batches
            event_extractor = EventsExtractor()
            for i in range(0, len(bitcoin_filings), batch_size):
                batch = bitcoin_filings[i:i + batch_size]
                await asyncio.gather(*(filing.extract_bitcoin_events(event_extractor) for filing in batch))
                if i + batch_size < len(bitcoin_filings):
                    await asyncio.sleep(delay)  # Wait for 1 second between batches

            return bitcoin_filings
    
    @staticmethod
    async def parse_bitcoin_events_for(bitcoin_filings: List["Bitcoin_Filing"]) -> List["Bitcoin_Filing"]:
        transformer = EventsTransformer()
        rpm = ai_settings.requests_per_minute
        tpm = ai_settings.tokens_per_minute
        chars_per_min = tpm * 3 # Conservatively assume 3 characters per token
        tokens_per_request = ai_settings.tokens_per_request
        sum_chars = 100000
        batch_size = len(bitcoin_filings)
        # If sum chars is less then chars_per_min then we can process all filings in one batch
        if sum_chars < chars_per_min and len(bitcoin_filings) < rpm:
            await asyncio.gather(*(filing.parse_bitcoin_events(transformer) for filing in bitcoin_filings))
            return bitcoin_filings
        else:
            batch_size = min(rpm, int(tpm / tokens_per_request))  # Number of requests per batch
            delay = 60  # Delay in seconds between batches
            event_extractor = EventsExtractor()
            for i in range(0, len(bitcoin_filings), batch_size):
                batch = bitcoin_filings[i:i + batch_size]
                await asyncio.gather(*(filing.parse_bitcoin_events(transformer) for filing in batch))
                if i + batch_size < len(bitcoin_filings):
                    await asyncio.sleep(delay)  # Wait for 1 second between batches

            return bitcoin_filings
    
    def get_bitcoin_total_holdings(self) -> Optional[TotalBitcoinHoldings]:
        return self.total_bitcoin_holdings
    
    def get_bitcoin_treasury_update(self) -> Optional[BitcoinTreasuryUpdate]:
        return self.bitcoin_treasury_update
    
    
    
    
    

        
    
