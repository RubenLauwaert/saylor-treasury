from typing import Enum


class BitcoinCompanyTag(str, Enum):
    MINER = "miner"
    ACTIVE_BTC_STRATEGY = "active_btc_strategy"
    ANNOUNCED_BTC_STRATEGY = "announced_btc_strategy"
    MENTIONED_BTC_IN_FILING = "mentioned_btc_in_filing"