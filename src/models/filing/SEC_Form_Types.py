from pydantic import BaseModel
from enum import Enum


class SEC_Form_Types(str, Enum):
    FORM_8K = "8-K"
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_S1 = "S-1"
    FORM_S3 = "S-3"
    FORM_4 = "4"
    FORM_3 = "3"
    FORM_5 = "5"
    FORM_13D = "13D"
    FORM_13G = "13G"
    FORM_144 = "144"
    FORM_11K = "11-K"
    FORM_20F = "20-F"
    FORM_40F = "40-F"
    FORM_6K = "6-K"
    FORM_DEF14A = "DEF 14A"
    FORM_424B5 = "424B5"
    FORM_424B4 = "424B4"
    FORM_424B3 = "424B3"
    FORM_424B2 = "424B2"
    FORM_424B1 = "424B1"
    FORM_424A = "424A"

    def __str__(self):
        return self.value
