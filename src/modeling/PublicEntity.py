from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
from src.modeling.EFTS_Response import EFTS_Hit_Source


class PublicEntityType(str, Enum):
    company = "company"
    fund = "fund"
    trust = "trust"
    government = "government"
    other = "other"

class PublicEntity(BaseModel):
    name: str = Field(..., description="The full legal name of the company.")
    ticker: Optional[str] = Field(None, description="The stock ticker symbol of the company, if applicable.")
    cik: str = Field(..., description="The Central Index Key (CIK) assigned by the SEC.")
    industry: Optional[str] = Field(None, description="The industry classification of the company, e.g., 'Technology'.")
    location: Optional[str] = Field(None, description="The primary location or headquarters of the company.")
    
    
    @classmethod
    def from_cik(cls, cik: str):
        entity_name = 'Test'
        return cls(name= entity_name, cik=cik)

def map_to_company(source: EFTS_Hit_Source ) -> PublicEntity:
    # Extract and clean up the name
    display_name = source.display_names[0] if source.display_names else None
    name = display_name.split("  ")[0] if display_name else None

    # Extract the CIK
    cik = source.ciks[0] if source.ciks else None


    # Create the Company object
    return PublicEntity(
        name=name,
        cik=cik,
    )
    