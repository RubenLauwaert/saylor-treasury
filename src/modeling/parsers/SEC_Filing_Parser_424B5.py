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


class TOC_Element(BaseModel):
    title: str
    page_index: str
    href_link: str


class TableOfContent(BaseModel):
    rows: List[TOC_Element]

    @staticmethod
    def get_content_between(soup: Tag, reference_href: str, page_number: str):
        logger = logging.getLogger(__class__.__name__)

        # Find the reference tag (e.g., <a> with specific href)
        reference_tag = soup.find(attrs={"name": reference_href.lstrip("#")})
        if not reference_tag:
            logger.info("Reference tag not found.")
            return None

        # Find the paragraph containing the specified page number (e.g., S-1)
        page_number_tag = soup.find(text=page_number)
        if not page_number_tag:
            logger.info("Page number tag not found.")
            return None

        logger.info(f"Reference tag: {reference_tag}")
        logger.info(f"Page number tag: {page_number_tag}")

        ref_tag_siblings = list(reference_tag.find_parent("p").next_siblings)[0:3]
        logger.info(ref_tag_siblings)


class SEC_Filing_Parser_424B5(BaseModel):

    @staticmethod
    def parse_filing(html: str):
        logger = logging.getLogger(__class__.__name__)
        soup = BeautifulSoup(html, "lxml")

        # Find table of contents for prospectus supplement and prospectus
        td_prospectus_supplement: Tag | None = soup.find(
            text="ABOUT THIS PROSPECTUS SUPPLEMENT"
        )
        td_prospectus: Tag | None = soup.find(text="ABOUT THIS PROSPECTUS")
        table_prospectus_supplement = td_prospectus_supplement.find_parent("table")
        table_prospectus = td_prospectus.find_parent("table")

        parsed_table_prospectus_supplement = None
        parsed_table_prospectus = None

        # If found parse the tables
        if table_prospectus_supplement is not None:
            parsed_table_prospectus_supplement = (
                SEC_Filing_Parser_424B5.parse_table_of_contents(
                    table_prospectus_supplement
                )
            )

        if table_prospectus is not None:
            parsed_table_prospectus = SEC_Filing_Parser_424B5.parse_table_of_contents(
                table_prospectus
            )

        first_row = parsed_table_prospectus_supplement.rows[0]
        content_between = SEC_Filing_Parser_424B5.get_content_between(
            soup, first_row.href_link, first_row.page_index
        )

        logger.info(
            f"Content between reference : {first_row.href_link} and page number : {first_row.page_index} is: \n\n {content_between}"
        )

    @staticmethod
    def parse_table_of_contents(table: Tag) -> TableOfContent:
        logger = logging.getLogger(__class__.__name__)
        toc_elements = []

        # Find all rows in the table
        rows = table.find_all("tr")
        for row in rows:
            parsed_row = SEC_Filing_Parser_424B5.parse_toc_row(row)
            if parsed_row:
                toc_elements.append(parsed_row)

        return TableOfContent(rows=toc_elements)

    @staticmethod
    def parse_toc_row(row: Tag) -> Union[TOC_Element, None]:
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

            result = TOC_Element(title=row_title, page_index=page_index, href_link=link)
        return result
