from pydantic import BaseModel, Field


from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from modeling.filing.SEC_Filing import SEC_Filing
from modeling.filing.util import FormType
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from modeling.parsers.util import (
    Table_Of_Content_Generic,
    Parsed_Filing_Generic_TOC,
    Filing_Section_Generic,
)


import asyncio


class Filing_10Q(SEC_Filing):
    """
    A 10-Q filing is a comprehensive report of a company's performance that must be submitted quarterly by all public companies to the Securities and Exchange Commission (SEC).
    This report provides unaudited financial statements and gives an overview of the company's financial situation during the quarter.
    It includes information such as the company's income, earnings per share, and cash flow, as well as management's discussion and analysis of the financial condition and results of operations.
    """

    table_of_content: Table_Of_Content_Generic = Field(
        default=None, description="Table of content of the 10-Q filing"
    )

    @field_validator("filing_metadata", check_fields=False)
    def validate_form_type(cls, value: SEC_Filing_Metadata):
        if not value.form == FormType.TEN_Q:
            raise ValueError(f"Filing is not of type {FormType.TEN_Q}")
        return value

    @classmethod
    async def from_metadata_async(
        cls, filing_metadata: SEC_Filing_Metadata
    ) -> "Filing_10Q":
        from modeling.parsers.sec_10q.SEC_Filing_Parser_10Q import (
            SEC_Filing_Parser_10Q,
        )

        # Call super method (load html_content)
        sec_filing = await super().from_metadata_async(filing_metadata)

        # Parse 10Q filing with specific parser
        filing_10q = SEC_Filing_Parser_10Q.parse_filing(
            sec_filing.content_html_str, sec_filing=sec_filing
        )

        return filing_10q

    @staticmethod
    async def from_metadatas_async(
        filing_metadatas: List[SEC_Filing_Metadata],
    ) -> List["Filing_10Q"]:
        batch_size = 10
        delay = 1.1  # Slightly more than 1 second to ensure we stay within the limit
        results = []

        for i in range(0, len(filing_metadatas), batch_size):
            batch = filing_metadatas[i : i + batch_size]
            tasks = [
                Filing_10Q.from_metadata_async(filing_metadata)
                for filing_metadata in batch
            ]
            results.extend(await asyncio.gather(*tasks))
            if i + batch_size < len(filing_metadatas):
                await asyncio.sleep(delay)

        return results

    def __str__(self):
        terminal_width = 80  # Assuming a standard terminal width of 80 characters
        title = "10-Q Filing"
        str_title_10_q = (
            f"\n{'-' * terminal_width}\n"
            f"{title.center(terminal_width)}\n"
            f"{'-' * terminal_width}\n"
        )

        # General information about SEC filing
        filing_str = super().__str__()

        # Table of content
        toc_title = "TABLE OF CONTENT"
        toc_str = (
            f"\n{'-' * terminal_width}\n"
            f"{toc_title.center(terminal_width)}\n"
            f"{'-' * terminal_width}\n\n"
        )

        toc_content_str = ""
        # Add only the titles of the table_of_content
        if self.table_of_content:
            for toc_element in self.table_of_content.elements:
                if toc_element.is_page_row:
                    toc_content_str += f"{toc_element.title}\n"
                elif toc_element.is_item_row:
                    toc_content_str += (
                        f"   {toc_element.item_str}     {toc_element.title}\n"
                    )
                else:
                    toc_content_str += f"     {toc_element.title}\n"

        return str_title_10_q + filing_str + toc_str + toc_content_str
