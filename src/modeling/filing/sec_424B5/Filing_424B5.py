from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from modeling.filing.SEC_Filing import SEC_Filing
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from modeling.parsers.SEC_Filing_Parser_424B5 import SEC_Filing_Parser_424B5
import asyncio


class Filing_424B5(SEC_Filing):
    """
    A 424B5 filing is a prospectus supplement that provides details about a securities offering by a company.
    It is used when a company sells securities under an already-approved shelf registration statement
    (typically filed using Form S-3 or F-3). The 424B5 provides the specific terms and conditions of the offering.
    """

    table_prospectus_supplement: Optional[str] = Field(
        default=None, description="Prospectus supplement table"
    )
    table_prospectus: Optional[str] = Field(
        default=None, description="Prospectus table"
    )

    @field_validator("filing_metadata", check_fields=False)
    def validate_form_type(cls, value: SEC_Filing_Metadata):
        if not value.form == "424B5":
            raise ValueError("Filing is not of type 424B5")
        return value

    @classmethod
    async def from_metadata_async(
        cls, filing_metadata: SEC_Filing_Metadata
    ) -> "Filing_424B5":

        # Call super method (load html_content)
        sec_filing = await super().from_metadata_async(filing_metadata)

        # Parse 424B5 filing with specific parser
        SEC_Filing_Parser_424B5.parse_filing(sec_filing.content_html_str)
        is_parsed = True

        return cls(**sec_filing.model_dump(exclude={"is_parsed"}), is_parsed=is_parsed)

    @staticmethod
    async def from_metadatas_async(
        filing_metadatas: List[SEC_Filing_Metadata],
    ) -> List["Filing_424B5"]:
        batch_size = 10
        delay = 1.1  # Slightly more than 1 second to ensure we stay within the limit
        results = []

        for i in range(0, len(filing_metadatas), batch_size):
            batch = filing_metadatas[i : i + batch_size]
            tasks = [
                Filing_424B5.from_metadata_async(filing_metadata)
                for filing_metadata in batch
            ]
            results.extend(await asyncio.gather(*tasks))
            if i + batch_size < len(filing_metadatas):
                await asyncio.sleep(delay)

        return results
