from typing import List, Union
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup, Tag
from modeling.parsers.util import Parsed_Filing_Generic, Filing_Section_Generic
from enum import Enum
from typing import Type
import logging
import warnings

# Suppress the BeautifulSoup warning for features="xml"
warnings.filterwarnings("ignore", category=UserWarning, message='.*features="xml".*')


class Filing_Parser_Generic(BaseModel):
    
    @staticmethod
    def get_cleaned_text(html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text()

    @staticmethod
    def parse_filing(html: str, titles_enum: Type[Enum]) -> Parsed_Filing_Generic:
        logger = logging.getLogger(__class__.__name__)
        soup = BeautifulSoup(html, "lxml")
        # Parsed filing
        parsed_filing = Parsed_Filing_Generic()
        sections = []
        # Get Titles
        titles = Filing_Parser_Generic.extract_titles(soup, titles_enum)

        for index, title in enumerate(titles):
            content = Filing_Parser_Generic.get_content_between_tags(
                soup, title, titles[index + 1] if index + 1 < len(titles) else None
            )
            parsed_filing.add_section(
                Filing_Section_Generic(title=title.text, content=content)
            )
        return parsed_filing

    @staticmethod
    def extract_titles(soup: BeautifulSoup, titles_enum: Type[Enum]) -> List[Tag]:
        logger = logging.getLogger(__class__.__name__)

        b_tags = Filing_Parser_Generic._extract_b_tags(soup)
        titles = [
            b_tag
            for b_tag in b_tags
            if b_tag.text.strip() in [title.value for title in titles_enum]
        ]
        logger.info(f"Titles found in the filing: {titles}")
        return titles

    @staticmethod
    def _extract_b_tags(soup: BeautifulSoup) -> List[Tag]:
        logger = logging.getLogger(__class__.__name__)

        b_tags = [
            soup.find(name="b", text=b_tag_str.text) for b_tag_str in soup.find_all("b")
        ]

        return b_tags

    @staticmethod
    def get_content_between_tags(
        soup: BeautifulSoup, start_tag: Tag, end_tag: Union[Tag, None]
    ) -> str:
        logger = logging.getLogger(__class__.__name__)
        content = ""
        start_tag_next_elements = list(start_tag.next_elements)
        for next_element in start_tag_next_elements:
            if next_element == end_tag:
                return content
            else:
                if next_element.name == "p":
                    content += next_element.text
                elif next_element.name == "table":
                    content += next_element.text
        return content
