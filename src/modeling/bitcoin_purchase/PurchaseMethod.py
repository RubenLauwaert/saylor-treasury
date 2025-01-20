# FILE: src/modeling/filing/PurchaseMethod.py

from pydantic import BaseModel
from enum import Enum


class PurchaseMethod(str, Enum):
    CASH_HOLDINGS = "CASH_HOLDINGS"
    ATM_ISSUANCE = "ATM_ISSUANCE"
    CONVERTIBLE_BOND_ISSUANCE = "CONVERTIBLE_BOND_ISSUANCE"
    PERPETUAL_PREFERRED_STOCK = "PERPETUAL_PREFERRED_STOCK"
    OTHER = "OTHER"



