from models.filing.sec_10q.Filing_10Q import Filing_10Q
from models.filing.SEC_Filing import SEC_Filing
from models.parsers.generic.Parser_Generic_TOC import Parser_Generic_TOC
from bs4 import BeautifulSoup
from models.parsers.util import *
import logging


class TOC_Titles_10Q(str, Enum):
    """
    Enum class for 10-Q table of content titles
    """

    FINANCIAL_INFORMATION = "FINANCIAL INFORMATION"
    RISK_FACTORS = "RISK_FACTORS"
    LEGAL_PROCEEDINGS = "LEGAL PROCEEDINGS"
    EXHIBITS = "EXHIBITS"
    OTHER_INFORMATION = "OTHER INFORMATION"


class SEC_Filing_Parser_10Q(BaseModel):

    @staticmethod
    def parse_filing(html: str, sec_filing: SEC_Filing) -> Filing_10Q:
        logger = logging.getLogger(__class__.__name__)
        soup = BeautifulSoup(html, "lxml-xml")
        # Extract 10-Q table of content
        toc = Parser_Generic_TOC._extract_table_of_content(soup, TOC_Titles_10Q)
        return Filing_10Q(
            **sec_filing.model_dump(exclude={"is_parsed", "table_of_content"}),
            table_of_content=toc,
            is_parsed=True
        )
