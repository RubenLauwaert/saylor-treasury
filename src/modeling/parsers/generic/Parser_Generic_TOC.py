from enum import Enum
import logging
from typing import Optional, Type, Union
from bs4 import BeautifulSoup, PageElement, ResultSet, Tag
from pydantic import BaseModel, Field
from modeling.parsers.util import (
    Filing_Section_Generic,
    Parsed_Filing_Generic_TOC,
    Table_Of_Content_Generic,
    TOC_Row_Generic,
    TOC_Pages,
    TOC_Supplement_Pages,
)


class Parser_Generic_TOC(BaseModel):

    @staticmethod
    def parse_filing(
        html: str, toc_titles: Type[Enum], is_toc_supplement: bool = False
    ) -> Optional[Parsed_Filing_Generic_TOC]:
        logger = logging.getLogger(__class__.__name__)
        soup = BeautifulSoup(html, "lxml")
        # Construct table of content
        toc = Parser_Generic_TOC._extract_table_of_content(
            soup, toc_titles, is_toc_supplement
        )
        if toc:
            # Extract content between table of content elements
            sections = Parser_Generic_TOC._extract_sections(soup, toc)
            # Return generic parsed filing toc
            return Parsed_Filing_Generic_TOC(table_of_content=toc, sections=sections)

        return None

    @staticmethod
    def _extract_table_of_content(
        soup: BeautifulSoup, toc_titles: Type[Enum], is_toc_supplement: bool = False
    ) -> Optional[Table_Of_Content_Generic]:
        logger = logging.getLogger(__class__.__name__)

        # Find the table of content in the html
        toc_table_tag = Parser_Generic_TOC._extract_toc_html_table_tag(
            soup, toc_titles, is_toc_supplement
        )
        # Initialize table of content
        toc = Table_Of_Content_Generic()

        if toc_table_tag:
            # Parse every row of the table
            tr_tags = toc_table_tag.find_all("tr")
            for tr_tag in tr_tags:
                toc_element = Parser_Generic_TOC._parse_toc_row(soup=soup, row=tr_tag)
                if toc_element:
                    toc.add_element(toc_element)
        return toc

    @staticmethod
    def _extract_toc_html_table_tag(
        soup: BeautifulSoup,
        toc_titles: Type[Enum],
        is_supplement_table: bool = False,
    ) -> Optional[PageElement]:

        toc_title_values = [title.value for title in toc_titles]
        toc_pages_values = (
            [page.value for page in TOC_Supplement_Pages]
            if is_supplement_table
            else [page.value for page in TOC_Pages]
        )
        # Find all tables
        tables: ResultSet[PageElement] = soup.find_all("table")
        # Check if TOC table
        for table in tables:
            # Check if table contains appropriate page numbers --> TOC table
            contains_page_numbers = any(
                td_tag.text.strip() in toc_pages_values
                for td_tag in table.find_all("td")
            )
            # Check if table contains (parts of) the given TOC titles --> TOC table
            contains_correct_title = any(
                any(
                    title.lower() in a_tag.text.lower().strip()
                    for title in toc_title_values
                )
                for a_tag in table.find_all("a")
            )
            if contains_page_numbers and contains_correct_title:
                return table

        return None

    @staticmethod
    def _parse_toc_row(soup: BeautifulSoup, row: Tag) -> Optional[TOC_Row_Generic]:
        logger = logging.getLogger(__class__.__name__)
        toc_element = None
        is_item_row = False
        is_page_row = False
        item_str = None
        page_str = None
        page_number = None
        title = ""
        href_link = ""
        element_index_in_soup = None

        # If row has no text, return None
        if len(row.text) == 0:
            return toc_element

        # Get columns of a table of contents row
        columns = row.find_all("td")

        # get links in row
        a_tags = row.find_all("a")

        # Filter rows with no link in it
        if len(a_tags) == 0:
            return toc_element

        # Find part tag in row
        part_tag = next(
            (column for column in columns if "part" in column.text.lower()), None
        )

        # Set part fields
        if part_tag:
            is_page_row = True
            page_str = part_tag.text

        # Find item tag in row
        item_tag = next(
            (column for column in columns if "item" in column.text.lower()), None
        )

        # Set item fields
        if item_tag:
            is_item_row = True
            item_str = item_tag.text

        # Find title tag in row based on longest link text
        title_tag = max(a_tags, key=lambda tag: len(tag.text)) if a_tags else None

        # Set title if title tag is found
        if title_tag:
            title = title_tag.text
            # Get href link and referenced tag out of title tag (a_tag)
            href_link = title_tag.get("href")
            # Find index of element in soup
            referenced_tag = soup.find(
                attrs={"name": href_link.lstrip("#")}
            ) or soup.find(id=href_link.lstrip("#"))

            element_index_in_soup = soup.find_all(True).index(referenced_tag)

        else:
            return toc_element

        # Find page number tag in row
        page_number_tag = next(
            (column for column in columns if column.text.isdigit()), None
        )

        # Set page number if page number tag is found
        if page_number_tag:
            page_number = int(page_number_tag.text)

        # Return TOC row
        return TOC_Row_Generic(
            is_item_row=is_item_row,
            is_page_row=is_page_row,
            item_str=item_str,
            page_str=page_str,
            title=title,
            page_number=page_number,
            href_link=href_link,
            element_index_in_soup=element_index_in_soup,
        )

    @staticmethod
    def _extract_content_between(
        soup: BeautifulSoup, start_index: int, end_index: Union[int, None]
    ) -> str:
        all_elements = soup.find_all(True)
        content_elements = (
            all_elements[start_index : end_index - 2]
            if end_index
            else all_elements[start_index:]
        )

        content = "".join(
            [
                element.text
                for element in content_elements
                if element.name == "p"
                or element.name == "table"
                or element.name == "font"
            ]
        )

        return content

    @staticmethod
    def _extract_sections(
        soup: BeautifulSoup, toc: Table_Of_Content_Generic
    ) -> list[Filing_Section_Generic]:
        sections = []
        for index, toc_element in enumerate(toc.elements):
            next_toc_element = (
                toc.elements[index + 1] if index + 1 < len(toc.elements) else None
            )
            toc_element_index = toc_element.element_index_in_soup
            next_toc_element_index = (
                next_toc_element.element_index_in_soup if next_toc_element else None
            )
            content = Parser_Generic_TOC._extract_content_between(
                soup, toc_element_index, next_toc_element_index
            )
            section = Filing_Section_Generic(title=toc_element.title, content=content)
            sections.append(section)
        return sections
