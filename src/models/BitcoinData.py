from pydantic import BaseModel, Field
from models.util import *

class BitcoinData(BaseModel):

    
    holding_statements_xbrl: List[BitcoinHoldingsStatement] = Field(default=[], description="The list of official bitcoin holdings statements, extracted from parsed XBRL 10Q filigns")
    fair_value_statements: List[BitcoinFairValueStatement] = Field(default=[], description="The list of official bitcoin fair value statements, extracted from parsed XBRL 10Q filigns")
    
    # Information extracted out of bitcoin filings with Generative AI
    bitcoin_events: List[BitcoinEvent] = Field(default=[], description="The list of bitcoin events.")
    holding_statements_gen_ai: List[BitcoinHoldingsStatement] = Field(default=[], description="The list of official bitcoin holdings statements, extracted from parsed (8K's) filings with Generative AI")
    treasury_updates_gen_ai: List[BitcoinTreasuryUpdate] = Field(default=[], description="The list of bitcoin treasury updates, extracted from parsed (8K's) filings with Generative AI")
    
    # Setters
    
    def set_bitcoin_tag(self, bitcoin_tag: BitcoinEntityTag):
        self.bitcoin_tag = bitcoin_tag