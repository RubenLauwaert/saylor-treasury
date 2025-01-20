# FILE: src/modeling/util.py

from datetime import date, timedelta
from enum import Enum


class ImportantDates(Enum):
    BTC_GENESIS_DATE = date(2009, 1, 3)
    MSTR_GENESIS_DATE = date(2020, 8, 11)
    TODAY = date.today()
    LAST_30_DAYS = TODAY - timedelta(days=30)
    
    
