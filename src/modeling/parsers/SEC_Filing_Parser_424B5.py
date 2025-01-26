from typing import Optional
import warnings
from pydantic import BaseModel, Field
import logging
from sec_parser.semantic_elements import *
import sec_parser as sp


class SEC_Filing_Parser_424B5(BaseModel):

    @staticmethod
    def parse_filing(html: str):
        logger = logging.getLogger(__class__.__name__)

        parser = sp.Edgar10QParser()

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Invalid section type for")
            elements: list = parser.parse(html)

        # Get prospectus (supplement) tables
        table_prospectus_supplement = None
        table_prospectus = None

        for index, element in enumerate(elements):
            if isinstance(element, TableElement):
                # retrieve prospectus supplement table
                if "ABOUT THIS PROSPECTUS SUPPLEMENT" in element.text:
                    logger.info(f"Parsing prospectus supplement table at index {index}")
                    # Parse prospectus tables
                    table_prospectus_supplement = (
                        SEC_Filing_Parser_424B5.parse_prospectus_table(element.text)
                    )
                # retrieve prospectus table
                elif "ABOUT THIS PROSPECTUS" in element.text:
                    logger.info(f"Parsing prospectus table at index {index}")
                    table_prospectus = SEC_Filing_Parser_424B5.parse_prospectus_table(
                        element.text
                    )

        for page in table_prospectus_supplement.values():
            for index, element in enumerate(elements):
                if page == element.text and len(element.text) < 20:
                    logger.info(
                        f"Found page {page} at index {index} in element {element} : {element.text[0:100] if len(element.text) > 100 else element.text}"
                    )

        for page in table_prospectus.values():
            for index, element in enumerate(elements):
                if page == element.text and len(element.text) < 20:
                    logger.info(
                        f"Found page {page} at index {index} in element {element} : {element.text[0:100] if len(element.text) > 100 else element.text}"
                    )

    @staticmethod
    def parse_prospectus_table(table: str) -> Optional[dict[str, str]]:
        logger = logging.getLogger(__class__.__name__)
        if not table:
            return None

        rows = table.split("\n")
        parsed_table = [row.split() for row in rows if row.strip()]

        # Filter out sublists that contain 'Page'
        filtered_parsed_table = [row for row in parsed_table if "Page" not in row]

        # Split filtered_parsed_table into separate lists of length two
        split_parsed_table = [
            filtered_parsed_table[i : i + 2]
            for i in range(0, len(filtered_parsed_table), 2)
        ]

        # Convert split_parsed_table to a dictionary
        result_dict = {}
        for pair in split_parsed_table:
            if len(pair) == 2:
                key_list, value_list = pair
                key = " ".join(key_list)
                value = "".join(value_list)
                result_dict[key] = value

        return result_dict
