
from typing import List
import warnings
from pydantic import BaseModel
import sec_parser as sp
import logging
from sec_parser import AbstractSemanticElement
from sec_parser.semantic_elements import *
import re

from models.filing.sec_8k.Item_8K import Item_8K, ItemCode_8K

class ItemExtractor(BaseModel):

    @staticmethod
    def extract_items(
        elements: List[AbstractSemanticElement], item_codes: List[str]
    ) -> List[Item_8K]:
        items = []
        item_index_dict: dict = {}
        for item_code in item_codes:
            if item_code is None:
                continue
            for index, element in enumerate(elements):
                if item_code in element.text and len(element.text) < 100:
                    item_index_dict[item_code] = index 
                    break
        # Create a dictionary to store relevant elements for each item
        item_elements_dict = {}
        sorted_item_codes = sorted(
            item_index_dict.keys(), key=lambda code: item_index_dict[code]
        )

        for i, item_code in enumerate(sorted_item_codes):
            start_index = item_index_dict[item_code]
            end_index = (
                item_index_dict[sorted_item_codes[i + 1]]
                if i + 1 < len(sorted_item_codes)
                else len(elements)
            )

            if start_index == end_index:
                item_elements_dict[item_code] = [elements[start_index]]
            else:
                item_elements_dict[item_code] = elements[start_index:end_index]

        # Loop over the item_elements_dict and create Items
        for item_code_str, elements in item_elements_dict.items():
            titles = [
                element.text
                for element in elements
                if isinstance(element, TitleElement)
            ]
            text_elements = [
                element for element in elements if isinstance(element, TextElement)
            ]
            merged_text_elements = [
                element for element in text_elements if "sec" in element.html_tag.name
            ]
            
            # Summary
            summary = " ".join(element.text for element in text_elements)
            # Cleaned summary
            cleaned_summary = ItemExtractor.clean_summary(summary)
    
                
            items.append(
                Item_8K(
                    code=ItemCode_8K.from_string(item_code_str),
                    subtitles=titles,
                    raw_text=cleaned_summary
                )
            )

        return items
    
    @staticmethod
    def clean_summary(summary: str) -> str:
        # Remove unwanted whitespace, newlines, and special characters
        summary = re.sub(r'\s+', ' ', summary)  # Replace multiple whitespace with a single space
        summary = re.sub(r'\\n', ' ', summary)  # Replace \n with a space
        summary = re.sub(r'\\u2009', ' ', summary)  # Replace \u2009 with a space
        summary = re.sub(r'\\xa0', ' ', summary)  # Replace \xa0 with a space
        summary = re.sub(r'\\', '', summary)  # Remove backslashes
        summary = re.sub(r'\s+', ' ', summary)  # Replace multiple spaces with a single space again
        summary = summary.strip()  # Remove leading and trailing whitespace
        return summary
    



class SEC_Filing_Parser_8K(BaseModel):

    @staticmethod
    def parse_filing(html: str, item_codes: List[str], ) -> List[Item_8K]:
        logger = logging.getLogger(SEC_Filing_Parser_8K.__name__)

        parser = sp.Edgar10QParser()

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Invalid section type for")
            elements: list = parser.parse(html)

        logger.info(f"Extracting item content for items: {item_codes}")
        items = ItemExtractor.extract_items(elements=elements, item_codes=item_codes)
        # logger.info(f"Succesfully extracted items: {[ {{ "item_code": item.code, "summary": item.summary[:100]}} for item in items]}")
        return items

