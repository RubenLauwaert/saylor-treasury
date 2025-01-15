# FILE: src/modeling/filing/PurchaseMethod.py

from pydantic import BaseModel
from enum import Enum


class AcquisitionMethodEnum(str, Enum):
    CASH_HOLDINGS = "CASH_HOLDINGS"
    ATM_ISSUANCE = "ATM_ISSUANCE"
    CONVERTIBLE_BOND_ISSUANCE = "CONVERTIBLE_BOND_ISSUANCE"
    PERPETUAL_PREFERRED_STOCK = "PERPETUAL_PREFERRED_STOCK"


class CashHoldings(BaseModel):
    amount: float


class AtmIssuance(BaseModel):
    amount: float
    date: str


class ConvertibleBondIssuance(BaseModel):
    amount: float
    maturity_date: str
    interest_rate: float


class PerpetualPreferredStock(BaseModel):
    amount: float
    dividend_rate: float
