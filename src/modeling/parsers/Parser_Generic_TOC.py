from enum import Enum
import logging
from typing import Optional, Type, Union
from bs4 import BeautifulSoup, PageElement, ResultSet, Tag
from pydantic import BaseModel, Field
from modeling.parsers.util import (
    Filing_Section_Generic,
    Parsed_Filing_Generic_TOC,
    Table_Of_Content_Generic,
    TOC_Element_Generic,
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
                toc_element = Parser_Generic_TOC.parse_toc_row(soup=soup, row=tr_tag)
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
                any(title in a_tag.text.strip() for title in toc_title_values)
                for a_tag in table.find_all("a")
            )

            if contains_page_numbers and contains_correct_title:
                return table

        return None

    @staticmethod
    def parse_toc_row(soup: BeautifulSoup, row: Tag) -> Optional[TOC_Element_Generic]:
        logger = logging.getLogger(__class__.__name__)
        toc_element = None

        # Get a_tag in row
        a_tag = row.find("a")

        # If row contains a link, parse row --> valid toc row
        if a_tag:
            # Get cells of row (td elements) and filter out cells containing '\xa0'
            cells = [cell for cell in row.find_all("td") if "\xa0" not in cell.text]
            # Extract item if cell text contains the word "item"
            item = next(
                (cell.text for cell in cells if "item" in cell.text.lower()), None
            )
            # Element with a_tag is the row_title
            title = a_tag.find_parent("td").text
            # Last element is page_index
            page_index = cells[-1].text if cells else ""
            # href of a_tag is the link
            link = a_tag.get("href")
            # Find index of element in soup
            referenced_tag = soup.find(attrs={"name": link.lstrip("#")})
            element_index_in_soup = soup.find_all(True).index(referenced_tag)
            toc_element = TOC_Element_Generic(
                item_str=item,
                title=title,
                page_index=page_index,
                href_link=link,
                element_index_in_soup=element_index_in_soup,
            )

        return toc_element

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
                if element.name == "p" or element.name == "table"
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
