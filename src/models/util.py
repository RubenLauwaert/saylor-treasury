from enum import Enum
from typing import Literal
from pydantic import BaseModel, model_validator

from datetime import datetime

class BitcoinCompanyTag(str, Enum):
    MINER = "miner"
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
