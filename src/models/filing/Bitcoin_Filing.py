import asyncio
from pydantic import BaseModel, Field
from typing import Optional, List, Literal

from models.filing.SEC_Filing import SEC_Filing
from services.ai.bitcoin_events import *
# from models.parsers.sec_10q.XBRL_Parser_10Q import Parser10QXBRL
from models.sec_edgar.efts.query import QueryHit
from models.parsers.generic.Filing_Parser_Generic import Filing_Parser_Generic


from config import openai_settings as ai_settings
# from models.util import BitcoinHoldingsStatement, BitcoinFairValueStatement





class Bitcoin_Filing(BaseModel):

    # Necessary data
    url: str
    accession_number: str
    file_type: str
    form_type: str
    file_date: str
    
    # Booleans
    did_parse_xbrl: bool = Field(default=False)
    did_extract_events_gen_ai: bool = Field(default=False)
    did_extract_holdings_gen_ai: bool = Field(default=False)
    

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
        
        
    # Setters
    
    def reset_all_states(self) -> "Bitcoin_Filing":
        self.did_parse_xbrl = False
        self.reset_gen_ai_states()
        return self
    
    def reset_gen_ai_states(self) -> "Bitcoin_Filing":
        self.did_extract_events_gen_ai = False
        self.did_extract_holdings_gen_ai = False
        return self
    
    
    # # official_bitcoin_holdings: List[BitcoinHoldingsStatement] = Field(default=[], description="The official bitcoin holdings statement for the entity. (only for 10Q's)")
    # # official_fair_value_statements: List[BitcoinFairValueStatement] = Field(default=[], description="The official bitcoin fair value statements for the entity. (only for 10Q's)")
    # # Getters
    # def get_bitcoin_acquisition_events(self) -> List[BitcoinEvent]:
    #     acquisition_events = [
    #         event for event in self.extracted_btc_events if event.event_type == BitcoinEventType.DEFINITIVE_BITCOIN_ACQUISITION
    #     ]
    #     return acquisition_events
    
    # def get_bitcoin_sale_events(self) -> List[BitcoinEvent]:
    #     sale_events = [
    #         event for event in self.extracted_btc_events if event.event_type == BitcoinEventType.DEFINITIVE_BITCOIN_SALE
    #     ]
    #     return sale_events
    
    # def get_bitcoin_total_holdings_events(self) -> List[BitcoinEvent]:
    #     total_holdings_events = [
    #         event for event in self.extracted_btc_events if event.event_type == BitcoinEventType.DISCLOSURE_OF_TOTAL_AMOUNT_OF_BITCOIN
    #     ]
    #     return total_holdings_events
    
    
    
    
    # Constructor


        
    # Async methods    
    
    # async def load_html_content(self) -> "Bitcoin_Filing":
    #     logger = logging.getLogger(self.__class__.__name__)
    #     has_raw_content = False
    #     raw_content_html = ""
    #     try:
    #         # Retrieve raw html content
    #         html_content = await SEC_Filing.get_raw_content_text(self.url)
    #         # Get raw text out of html 
    #         raw_text = Filing_Parser_Generic.get_cleaned_text(html_content)
    #         self.raw_text = raw_text
    #         self.has_raw_content = True
    #     except Exception as e:
    #         logger.error(f"Failed to load html content for filing {self.url}: {e}")
    #     return self
        
    
    
    # async def extract_bitcoin_events(self, extractor: EventsExtractor) -> "Bitcoin_Filing":
    #     logger = logging.getLogger(self.__class__.__name__)
    #     try:    
    #         if self.has_raw_content and len(self.raw_text) > 0:
    #             extracted_events = await extractor.extract_events(self.raw_text)
    #             self.extracted_btc_events = extracted_events.events
    #             self.has_extracted_events = True
    #             logger.info(f"Extracted bitcoin events from filing {self.url}")
    #         else:
    #             raise ValueError("No raw content available")
                
    #     except Exception as e:
    #         logger.error(f"Failed to extract bitcoin events from filing {self.url}: {e}")
    #     return self
    
    
    # async def parse_bitcoin_events(self, transformer: EventsTransformer) -> "Bitcoin_Filing":
    #     logger = logging.getLogger(self.__class__.__name__)
        
    #     try:
    #         # Try to transform events to bitcoin total holdings
    #             total_holdings_events = self.get_bitcoin_total_holdings_events()
    #             if len(total_holdings_events) > 0:
    #                 parsed_btc_holdings = await transformer.transform_bitcoin_total_holdings_events(total_holdings_events)
    #                 if parsed_btc_holdings is not None:
    #                     self.total_bitcoin_holdings = parsed_btc_holdings
    #                     self.has_total_bitcoin_holdings = True
    #                     logger.info(f"Transformed total bitcoin holdings for filing {self.url}")
    #             #Try to transform events to bitcoin treasury update
    #             acquisition_events = self.get_bitcoin_acquisition_events()
    #             if len(acquisition_events) > 0:
    #                 parsed_treasury_update = await transformer.transform_bitcoin_purchase_events(acquisition_events)
    #                 if parsed_treasury_update is not None:
    #                     self.bitcoin_treasury_update = parsed_treasury_update
    #                     self.has_bitcoin_treasury_update = True
    #                     logger.info(f"Transformed bitcoin purchases for filing {self.url}")
    #     except Exception as e:
    #         logger.error(f"Failed to transform bitcoin events for filing {self.url}: {e}")
            
            
    # # async def extract_official_bitcoin_holdings(self, ticker: str) -> "Bitcoin_Filing":
    # #     logger = logging.getLogger(self.__class__.__name__)
    # #     try:
    # #         if self.file_type == "10-Q" and self.parsed_official_10q_statements == False:
    # #             # Extract official bitcoin holdings
    # #             xbrl_url = self.url.replace(".htm", "_htm.xml")
    # #             xbrl_content = await SEC_Filing.get_raw_content_text(xbrl_url)
    # #             parsed_content = Parser10QXBRL(xbrl_string=xbrl_content, ticker=ticker)
    # #             self.official_bitcoin_holdings = await parsed_content.extract_bitcoin_holdings()
    # #             self.official_fair_value_statements = await parsed_content.extract_bitcoin_fair_value()
    # #             self.parsed_official_10q_statements = True
    # #     except Exception as e:
    # #         logger.error(f"Failed to extract official bitcoin holdings for filing {self.url}: {e}")
    # #     return self
        
    
    
    # @staticmethod
    # async def load_html_content_for(bitcoin_filings: List["Bitcoin_Filing"]) -> List["Bitcoin_Filing"]:
    #     batch_size = 10  # Number of requests per batch
    #     delay = 1.1  # Delay in seconds between batches
    #     for i in range(0, len(bitcoin_filings), batch_size):
    #         batch = bitcoin_filings[i:i + batch_size]
    #         await asyncio.gather(*(filing.load_html_content() for filing in batch))
    #         if i + batch_size < len(bitcoin_filings):
    #             await asyncio.sleep(delay)  # Wait for 1 second between batches

    #     return bitcoin_filings
    
    # @staticmethod
    # async def extract_bitcoin_events_for(bitcoin_filings: List["Bitcoin_Filing"]) -> List["Bitcoin_Filing"]:
    #     rpm = ai_settings.requests_per_minute
    #     tpm = ai_settings.tokens_per_minute
    #     chars_per_min = tpm * 3 # Conservatively assume 3 characters per token
    #     tokens_per_request = ai_settings.tokens_per_request
    #     event_extractor = EventsExtractor()
    #     sum_chars = sum([len(filing.raw_text) for filing in bitcoin_filings])
    #     logging.info(f"Sum of chars: {sum_chars}")
    #     batch_size = len(bitcoin_filings)
    #     # If sum chars is less then chars_per_min then we can process all filings in one batch
    #     if sum_chars < chars_per_min and len(bitcoin_filings) < rpm:
    #         await asyncio.gather(*(filing.extract_bitcoin_events(event_extractor) for filing in bitcoin_filings))
    #         return bitcoin_filings
    #     else:
    #         batch_size = min(rpm, int(tpm / tokens_per_request))  # Number of requests per batch
    #         delay = 60  # Delay in seconds between batches
    #         event_extractor = EventsExtractor()
    #         for i in range(0, len(bitcoin_filings), batch_size):
    #             batch = bitcoin_filings[i:i + batch_size]
    #             await asyncio.gather(*(filing.extract_bitcoin_events(event_extractor) for filing in batch))
    #             if i + batch_size < len(bitcoin_filings):
    #                 await asyncio.sleep(delay)  # Wait for 1 second between batches

    #         return bitcoin_filings
    
    # @staticmethod
    # async def parse_bitcoin_events_for(bitcoin_filings: List["Bitcoin_Filing"]) -> List["Bitcoin_Filing"]:
    #     transformer = EventsTransformer()
    #     rpm = ai_settings.requests_per_minute
    #     tpm = ai_settings.tokens_per_minute
    #     chars_per_min = tpm * 3 # Conservatively assume 3 characters per token
    #     tokens_per_request = ai_settings.tokens_per_request
    #     sum_chars = 100000
    #     batch_size = len(bitcoin_filings)
    #     # If sum chars is less then chars_per_min then we can process all filings in one batch
    #     if sum_chars < chars_per_min and len(bitcoin_filings) < rpm:
    #         await asyncio.gather(*(filing.parse_bitcoin_events(transformer) for filing in bitcoin_filings))
    #         return bitcoin_filings
    #     else:
    #         batch_size = min(rpm, int(tpm / tokens_per_request))  # Number of requests per batch
    #         delay = 60  # Delay in seconds between batches
    #         event_extractor = EventsExtractor()
    #         for i in range(0, len(bitcoin_filings), batch_size):
    #             batch = bitcoin_filings[i:i + batch_size]
    #             await asyncio.gather(*(filing.parse_bitcoin_events(transformer) for filing in batch))
    #             if i + batch_size < len(bitcoin_filings):
    #                 await asyncio.sleep(delay)  # Wait for 1 second between batches

    #         return bitcoin_filings
        
        
    # # @staticmethod
    # # async def extract_official_bitcoin_holdings_for(bitcoin_filings: List["Bitcoin_Filing"], ticker: str) -> List["Bitcoin_Filing"]:
         
    # #     batch_size = 10  # Number of requests per batch
    # #     delay = 1.1  # Delay in seconds between batches
    # #     for i in range(0, len(bitcoin_filings), batch_size):
    # #         batch = bitcoin_filings[i:i + batch_size]
    # #         await asyncio.gather(*(filing.extract_official_bitcoin_holdings(ticker) for filing in batch))
    # #         if i + batch_size < len(bitcoin_filings):
    # #             await asyncio.sleep(delay)  # Wait for 1 second between batches

    # #     return bitcoin_filings
        
        
    
    # def get_bitcoin_total_holdings(self) -> Optional[TotalBitcoinHoldings]:
    #     return self.total_bitcoin_holdings
    
    # def get_bitcoin_treasury_update(self) -> Optional[BitcoinTreasuryUpdate]:
    #     return self.bitcoin_treasury_update
    
    
    
    
    

        
    
