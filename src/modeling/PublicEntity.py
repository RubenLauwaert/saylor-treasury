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
    def map_to_entity(cls, display_name: str, cik: str) -> "PublicEntity":
        """
        Create a PublicEntity object from display_name + CIK,
        inferring ticker if present and entity type from keywords.
        """

        # 1. Infer entity type by simple keyword matching in the name.
        lower_name = display_name.lower()
        if "trust" in lower_name:
            inferred_type = PublicEntityType.trust
        elif "fund" in lower_name or "funds" in lower_name:
            inferred_type = PublicEntityType.fund
        elif any(keyword in lower_name for keyword in ("inc", "corp", "ltd")):
            inferred_type = PublicEntityType.company
        else:
            inferred_type = PublicEntityType.other

        # 2. Attempt to extract a ticker from parentheses
        #    We'll look for anything in (...) that is NOT "CIK ..." and not purely numeric.
        import re

        parentheticals = re.findall(r"\(([^)]*)\)", display_name)
        ticker_val = None

        for text_in_parens in parentheticals:
            # e.g. text_in_parens could be "MSTR", "CIK 0001050446", "FLD, FLDD, FLDDU, FLDDW"
            # Skip if it starts with "CIK" or if it's purely digits
            if text_in_parens.strip().startswith("CIK"):
                continue
            # If it's purely digits (or digits plus spaces), skip
            if text_in_parens.replace(" ", "").isdigit():
                continue

            # If the text has commas (multiple tickers), pick the first
            if "," in text_in_parens:
                possible_tickers = [x.strip() for x in text_in_parens.split(",")]
                # pick the first non-empty
                ticker_val = possible_tickers[0] if possible_tickers else None
            else:
                ticker_val = text_in_parens.strip()

            # If we found something that doesn't look like "CIK ..." or numeric, we stop
            if ticker_val:
                break

        # 3. Build the PublicEntity object
        return cls(
            name=display_name, cik=cik, ticker=ticker_val, entity_type=inferred_type
        )
