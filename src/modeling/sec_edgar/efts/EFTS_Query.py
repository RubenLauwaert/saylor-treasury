from pydantic import BaseModel, Field
from datetime import date


class EFTSQuery(BaseModel):
    lucene_query: str
    dateRange: str = Field(default="custom")
    startdt: date
    enddt: date


# Example usage
base_bitcoin_8k_company_query = EFTSQuery(
    lucene_query="(bitcoin OR Bitcoin) AND (FORM 8-K) AND NOT Trust",
    startdt=date(2024, 12, 15),
    enddt=date.today(),
)

base_bitcoin_8k_mining_company_query = EFTSQuery(
    lucene_query="(bitcoin OR Bitcoin) AND (FORM 8-K) AND NOT Trust AND mining",
    startdt=date(2024, 12, 15),
    enddt=date.today(),
)

base_bitcoin_balance_sheet_query = EFTSQuery(
    lucene_query="(bitcoin OR Bitcoin) AND (purchase OR purchased OR acquired OR added)",
    startdt=date(2024, 12, 15),
    enddt=date.today(),
)
