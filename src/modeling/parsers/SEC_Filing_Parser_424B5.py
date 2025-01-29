from enum import Enum
from typing import List, Optional, Union
import warnings
from pydantic import BaseModel, Field
import logging
from modeling.filing.SEC_Filing import SEC_Filing
from modeling.filing.sec_424B5.Filing_424B5 import Filing_424B5
from modeling.parsers.Filing_Parser_Generic import Filing_Parser_Generic
from modeling.parsers.Parser_Generic_TOC import Parser_Generic_TOC
from modeling.parsers.util import (
    Parsed_Filing_Generic_TOC,
    TOC_Element_Generic,
    Parsed_Filing_Generic,
)
from bs4 import BeautifulSoup, Tag, PageElement


class Prospectus_Titles(Enum):

    SUMMARY = "SUMMARY"
    RISK_FACTORS = "RISK FACTORS"
    THE_OFFERING = "THE OFFERING"
    USE_OF_PROCEEDS = "USE OF PROCEEDS"
    CAPITALIZATION = "CAPITALIZATION"
    DILUTION = "DILUTION"
    DESCRIPTION_OF_SECURITIES = "DESCRIPTION OF SECURITIES"
    PLAN_OF_DISTRIBUTION = "PLAN OF DISTRIBUTION"
    LEGAL_MATTERS = "LEGAL MATTERS"
    EXPERTS = "EXPERTS"
    WHERE_YOU_CAN_FIND_MORE_INFORMATION = "WHERE YOU CAN FIND MORE INFORMATION"
    INCORPORATION_OF_CERTAIN_INFORMATION_BY_REFERENCE = (
        "INCORPORATION OF CERTAIN INFORMATION BY REFERENCE"
    )


class SEC_Filing_Parser_424B5(BaseModel):

    @staticmethod
    def parse_filing(html: str, sec_filing: SEC_Filing) -> Filing_424B5:
        logger = logging.getLogger(__class__.__name__)
        sections = []
        # Use generic TOC parser to parse prospectus toc and sections
        prospectus = Parser_Generic_TOC.parse_filing(html, Prospectus_Titles)
        # Use generic TOC parser to parse prospectus supplement toc and sections
        prospectus_supplement = Parser_Generic_TOC.parse_filing(
            html, Prospectus_Titles, is_toc_supplement=True
        )
        # If no table of contents in the filing, Use generic parser
        if not prospectus and not prospectus_supplement:
            parsed_filing_generic = Filing_Parser_Generic.parse_filing(
                html, Prospectus_Titles
            )
            sections = parsed_filing_generic.sections

        return Filing_424B5(
            **sec_filing.model_dump(
                exclude={
                    "is_parsed",
                    "sections",
                    "prospectus",
                    "prospectus_supplement",
                }
            ),
            prospectus_supplement=prospectus_supplement,
            prospectus=prospectus,
            sections=sections,
            is_parsed=True,
        )
