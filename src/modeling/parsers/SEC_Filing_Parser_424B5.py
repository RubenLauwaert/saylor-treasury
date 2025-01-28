from enum import Enum
from typing import List, Optional, Union
import warnings
from pydantic import BaseModel, Field
import logging
from sec_parser.semantic_elements import *
import sec_parser as sp
from sec_parser.semantic_elements.abstract_semantic_element import (
    AbstractSemanticElement,
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


class Prospectus_Supplement_Pages(Enum):
    S_1 = "S-1"
    S_2 = "S-2"
    S_3 = "S-3"
    S_4 = "S-4"
    S_5 = "S-5"
    S_6 = "S-6"
    S_7 = "S-7"
    S_8 = "S-8"
    S_9 = "S-9"
    S_10 = "S-10"


class Prospectus_Pages(Enum):
    P_1 = "1"
    P_2 = "2"
    P_3 = "3"
    P_4 = "4"
    P_5 = "5"
    P_6 = "6"
    P_7 = "7"
    P_8 = "8"
    P_9 = "9"
    P_10 = "10"


class TOC_Element_424B5(BaseModel):
    title: str
    page_index: Optional[str]
    href_link: Optional[str]


class TableOfContent_424B5(BaseModel):
    rows: List[TOC_Element_424B5]

    def get_row_content(self, soup: Tag, row_index: int) -> str:
        logger = logging.getLogger(__class__.__name__)

        if row_index > len(self.rows) - 1:
            logger.error("Row index out of bounds.")
            return None

        toc_row = self.rows[row_index]

        start_tag = soup.find(attrs={"name": toc_row.href_link.lstrip("#")})
        end_tag = None
        if row_index == len(self.rows) - 1:
            end_tag = soup.find(text=toc_row.page_index)
        else:
            next_toc_row = self.rows[row_index + 1]
            end_tag = soup.find(attrs={"name": next_toc_row.href_link.lstrip("#")})

        start_tag_next_elements = list(start_tag.next_elements)
        content = ""
        for next_element in start_tag_next_elements:
            if next_element == end_tag:
                return content
            else:
                if next_element.name == "p":
                    content += next_element.text
        return None


class Section_424B5(BaseModel):
    toc_element: TOC_Element_424B5
    content: Optional[str]
    is_prospectus_supplement: bool


class SEC_Filing_Parser_424B5(BaseModel):

    @staticmethod
    def parse_filing(html: str) -> List[Section_424B5]:
        logger = logging.getLogger(__class__.__name__)
        soup = BeautifulSoup(html, "lxml")

        # Extract table of contents for prospectus supplement and prospectus
        toc_prospectus_supplement = (
            SEC_Filing_Parser_424B5.extract_toc_prospectus_supplement(soup)
        )

        toc_prospectus = SEC_Filing_Parser_424B5.extract_toc_prospectus(soup)

        # Generate Sections from the table of contents
        sections = []
        # Generate Sections for toc prospectus supplements
        if toc_prospectus_supplement:
            for index, toc_element in enumerate(toc_prospectus_supplement.rows):
                content = toc_prospectus_supplement.get_row_content(soup, index)
                sections.append(
                    Section_424B5(
                        toc_element=toc_element,
                        content=content,
                        is_prospectus_supplement=True,
                    )
                )

        # Generate Sections for toc prospectus
        if toc_prospectus:
            for index, toc_element in enumerate(toc_prospectus.rows):
                content = toc_prospectus.get_row_content(soup, index)
                sections.append(
                    Section_424B5(
                        toc_element=toc_element,
                        content=content,
                        is_prospectus_supplement=False,
                    )
                )

        # If no table of contents in the filing, parse bold paragraphs as titles
        if not toc_prospectus_supplement and not toc_prospectus:
            b_tags = soup.find_all("b")
            titles = [
                b_tag.text
                for b_tag in b_tags
                if b_tag.text.strip() in [title.value for title in Prospectus_Titles]
            ]
            logger.info(f"Found {titles} titles in the filing.")

            # Get content between titles
            for index, title in enumerate(titles):
                start_tag = soup.find("b", text=title)
                logger.info(f"Found start tag: {start_tag}")
                end_tag = None
                if index < len(titles) - 1:
                    end_tag = soup.find("b", text=titles[index + 1])
                # Parse content between start_tag and end_tag
                start_tag_next_elements = list(start_tag.next_elements)
                logger.info(f"Found {len(start_tag_next_elements)} next elements.")
                content = ""
                for next_element in start_tag_next_elements:
                    if next_element == end_tag:
                        logger.info("End tag found.")
                        break
                    else:
                        if next_element.name == "p":
                            content += next_element.text
                sections.append(
                    Section_424B5(
                        toc_element=TOC_Element_424B5(
                            title=title, page_index=None, href_link=None
                        ),
                        content=content,
                        is_prospectus_supplement=False,
                    )
                )
        logger.info(f"Parsed {len(sections)} sections.")
        return sections

    @staticmethod
    def extract_toc_prospectus_supplement(soup: Tag) -> Optional[TableOfContent_424B5]:
        logger = logging.getLogger(__class__.__name__)
        tables = soup.find_all("table")
        for table in tables:
            # Check if table contains an <a> tag with common prospectus titles
            a_tags = table.find_all("a")
            for a_tag in a_tags:
                if a_tag.text.strip() in [title.value for title in Prospectus_Titles]:
                    # Check if it is prospectus supplement or prospectus
                    td_tags = table.find_all("td")
                    for td_tag in td_tags:
                        if td_tag.text.strip() in [
                            page.value for page in Prospectus_Supplement_Pages
                        ]:
                            return SEC_Filing_Parser_424B5.parse_table_of_contents(
                                table
                            )
        return None

    @staticmethod
    def extract_toc_prospectus(soup: Tag) -> Optional[TableOfContent_424B5]:
        tables = soup.find_all("table")
        for table in tables:
            # Check if table contains an <a> tag with common prospectus titles
            a_tags = table.find_all("a")
            for a_tag in a_tags:
                if a_tag.text.strip() in [title.value for title in Prospectus_Titles]:
                    # Check if it is prospectus supplement or prospectus
                    td_tags = table.find_all("td")
                    for td_tag in td_tags:
                        if td_tag.text.strip() in [
                            page.value for page in Prospectus_Pages
                        ]:
                            return SEC_Filing_Parser_424B5.parse_table_of_contents(
                                table
                            )
        return None

    @staticmethod
    def parse_table_of_contents(table: Tag) -> TableOfContent_424B5:
        logger = logging.getLogger(__class__.__name__)
        toc_elements = []

        # Find all rows in the table
        rows = table.find_all("tr")
        for row in rows:
            parsed_row = SEC_Filing_Parser_424B5.parse_toc_row(row)
            if parsed_row:
                toc_elements.append(parsed_row)

        return TableOfContent_424B5(rows=toc_elements)

    @staticmethod
    def parse_toc_row(row: Tag) -> Union[TOC_Element_424B5, None]:
        logger = logging.getLogger(__class__.__name__)
        result = None

        # Get a_tag in row
        a_tag = row.find("a")

        # If row contains a link, parse row --> valid toc row
        if a_tag:
            # Get cells of row (td elements) and filter out cells containing '\xa0'
            cells = [cell for cell in row.find_all("td") if "\xa0" not in cell.text]

            # Element with a_tag is the row_title
            row_title = a_tag.find_parent("td").text
            # Last element is page_index
            page_index = cells[-1].text if cells else ""
            # href of a_tag is the link
            link = a_tag.get("href")

            result = TOC_Element_424B5(
                title=row_title, page_index=page_index, href_link=link
            )
        return result
