from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List


class PublicEntityType(str, Enum):
    company = "company"
    fund = "fund"
    trust = "trust"
    government = "government"
    other = "other"


class PublicEntity(BaseModel):
    name: str = Field(..., description="The full legal name of the company.")
    ticker: Optional[str] = Field(
        None, description="The stock ticker symbol of the company, if applicable."
    )
    cik: str = Field(
        ..., description="The Central Index Key (CIK) assigned by the SEC."
    )
    industry: Optional[str] = Field(
        None,
        description="The industry classification of the company, e.g., 'Technology'.",
    )
    location: Optional[str] = Field(
        None, description="The primary location or headquarters of the company."
    )

    # New optional field for the type of public entity
    entity_type: Optional[PublicEntityType] = Field(
        None, description="The type of the public entity (company, fund, trust, etc.)."
    )

    @classmethod
    def map_to_entity(cls, display_name: str) -> "PublicEntity":
        """
        Create a PublicEntity object from display_name,
        inferring ticker if present and entity type from keywords.
        """

        # 1. Extract CIK from the display_name
        import re

        cik_match = re.search(r"CIK\s*(\d+)", display_name)
        cik = cik_match.group(1) if cik_match else None

        # 2. Infer entity type by simple keyword matching in the name.
        lower_name = display_name.lower()
        if "trust" in lower_name:
            inferred_type = PublicEntityType.trust
        elif "fund" in lower_name or "funds" in lower_name:
            inferred_type = PublicEntityType.fund
        elif any(keyword in lower_name for keyword in ("inc", "corp", "ltd")):
            inferred_type = PublicEntityType.company
        else:
            inferred_type = PublicEntityType.other

        # 3. Attempt to extract a ticker from parentheses
        parentheticals = re.findall(r"\(([^)]*)\)", display_name)
        ticker_val = None

        for text_in_parens in parentheticals:
            # Skip if it starts with "CIK" or if it's purely digits
            if text_in_parens.strip().startswith("CIK"):
                continue
            if text_in_parens.replace(" ", "").isdigit():
                continue

            # If the text has commas (multiple tickers), pick the first
            if "," in text_in_parens:
                possible_tickers = [x.strip() for x in text_in_parens.split(",")]
                ticker_val = possible_tickers[0] if possible_tickers else None
            else:
                ticker_val = text_in_parens.strip()

            if ticker_val:
                break

        # 4. Extract the name before the ticker symbol
        name_before_ticker = (
            display_name.split(f"({ticker_val})")[0].strip()
            if ticker_val
            else display_name
        )

        # 5. Clean up the name by removing redundant data
        name_cleaned = re.sub(r"\s*\(.*?\)\s*", "", name_before_ticker).strip()

        # 6. Build the PublicEntity object
        return cls(
            name=name_cleaned, cik=cik, ticker=ticker_val, entity_type=inferred_type
        )
