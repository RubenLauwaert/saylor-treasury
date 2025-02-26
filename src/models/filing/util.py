from enum import Enum
from pydantic import BaseModel, Field


class FormType(str, Enum):
    EIGHT_K = "8-K"
    FOUR_TWO_FOUR_B_FIVE = "424B5"
    TEN_Q = "10-Q"
    TEN_K = "10-K"

    def __str__(self):
        return self.value
