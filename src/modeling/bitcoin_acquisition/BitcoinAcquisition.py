from typing import Union
from modeling.bitcoin_acquisition.AcquisitionMethod import *


class BitcoinAcquisitio(BaseModel):
    date: str
    amount: float
    price: float
    purchase_method: AcquisitionMethodEnum
    method_details: Union[
        CashHoldings, AtmIssuance, ConvertibleBondIssuance, PerpetualPreferredStock
    ]
