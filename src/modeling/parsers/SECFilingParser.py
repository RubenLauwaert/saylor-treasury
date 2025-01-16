from enum import Enum
from typing import List, Optional
import warnings
from pydantic import BaseModel
import sec_parser as sp
import logging
from sec_parser import SemanticTree, TreeNode, AbstractSemanticElement
from sec_parser.processing_steps import (
    TopSectionManagerFor10Q,
    IndividualSemanticElementExtractor,
    TopSectionTitleCheck,
)
from sec_parser.semantic_elements import *
import re
from transformers import pipeline


class ItemCode(Enum):
    # Section 1: Registrant’s Business and Operations
    ITEM_1_01 = "Item 1.01 Entry into a Material Definitive Agreement"
    ITEM_1_02 = "Item 1.02 Termination of a Material Definitive Agreement"
    ITEM_1_03 = "Item 1.03 Bankruptcy or Receivership"
    ITEM_1_04 = (
        "Item 1.04 Mine Safety—Reporting of Shutdowns and Patterns of Violations"
    )

    # Section 2: Financial Information
    ITEM_2_01 = "Item 2.01 Completion of Acquisition or Disposition of Assets"
    ITEM_2_02 = "Item 2.02 Results of Operations and Financial Condition"
    ITEM_2_03 = "Item 2.03 Creation of a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement of a Registrant"
    ITEM_2_04 = "Item 2.04 Triggering Events That Accelerate or Increase a Direct Financial Obligation or an Obligation under an Off-Balance Sheet Arrangement"
    ITEM_2_05 = "Item 2.05 Costs Associated with Exit or Disposal Activities"
    ITEM_2_06 = "Item 2.06 Material Impairments"

    # Section 3: Securities and Trading Markets
    ITEM_3_01 = "Item 3.01 Notice of Delisting or Failure to Satisfy a Continued Listing Rule or Standard; Transfer of Listing"
    ITEM_3_02 = "Item 3.02 Unregistered Sales of Equity Securities"
    ITEM_3_03 = "Item 3.03 Material Modification to Rights of Security Holders"

    # Section 4: Matters Related to Accountants and Financial Statements
    ITEM_4_01 = "Item 4.01 Changes in Registrant’s Certifying Accountant"
    ITEM_4_02 = "Item 4.02 Non-Reliance on Previously Issued Financial Statements or a Related Audit Report or Completed Interim Review"

    # Section 5: Corporate Governance and Management
    ITEM_5_01 = "Item 5.01 Changes in Control of Registrant"
    ITEM_5_02 = "Item 5.02 Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers"
    ITEM_5_03 = "Item 5.03 Amendments to Articles of Incorporation or Bylaws; Change in Fiscal Year"
    ITEM_5_04 = "Item 5.04 Temporary Suspension of Trading under Registrant’s Employee Benefit Plans"
    ITEM_5_05 = "Item 5.05 Amendments to the Registrant’s Code of Ethics, or Waiver of a Provision of the Code of Ethics"

    # Section 6: Asset-Backed Securities
    ITEM_6_01 = "Item 6.01 ABS Informational and Computational Material"
    ITEM_6_02 = "Item 6.02 Change of Servicer or Trustee"
    ITEM_6_03 = "Item 6.03 Change in Credit Enhancement or Other External Support"
    ITEM_6_04 = "Item 6.04 Failure to Make a Required Distribution"
    ITEM_6_05 = "Item 6.05 Securities Act Updating Disclosure"

    # Section 7: Regulation FD
    ITEM_7_01 = "Item 7.01 Regulation FD Disclosure"

    # Section 8: Other Events
    ITEM_8_01 = "Item 8.01 Other Events"

    # Section 9: Financial Statements and Exhibits
    ITEM_9_01 = "Item 9.01 Financial Statements and Exhibits"

    @staticmethod
    def from_string(item_code_str: str) -> Optional["ItemCode"]:
        item_code_enum = f"ITEM_{item_code_str.replace('.', '_')}"
        return ItemCode.__members__.get(item_code_enum, None)

    @staticmethod
    def map_item_codes(item_code_strs: List[str]) -> List[Optional["ItemCode"]]:
        return [ItemCode.from_string(code) for code in item_code_strs]


class Item(BaseModel):
    code: Optional[ItemCode]
    subtitles: List[str]
    summary: List[str]

    class Config:
        use_enum_values = True


class ItemExtractor(BaseModel):

    @staticmethod
    def extract_items(
        elements: List[AbstractSemanticElement], item_codes: List[str]
    ) -> List[Item]:
        items = []
        item_index_dict: dict = {}
        logging.info(elements[17].text)
        for item_code in item_codes:
            if item_code is None:
                continue
            for index, element in enumerate(elements):
                if item_code in element.text:
                    item_index_dict[item_code] = index
                    break
        logging.info(item_index_dict)
        # Create a dictionary to store relevant elements for each item
        item_elements_dict = {}
        sorted_item_codes = sorted(
            item_index_dict.keys(), key=lambda code: item_index_dict[code]
        )
        logging.info(sorted_item_codes)

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

        logging.info(f"Item Elements Dictionary: {item_elements_dict}")

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
            summary = " ".join(element.text for element in elements)
            items.append(
                Item(
                    code=ItemCode.from_string(item_code_str),
                    summary=[summary],
                    subtitles=titles,
                )
            )

        return items


class SEC_Filing_Parser(BaseModel):
    @staticmethod
    def parse_filing(html: str) -> Optional[List[str]]:
        tree = SemanticTree.from_html(html)
        print(f"Parsed Tree: {tree}")
        return ItemExtractor.extract_items(tree)

    @staticmethod
    def parse_filing_via_lib(html: str, item_codes: List[str]) -> Optional[List[Item]]:

        parser = sp.Edgar10QParser()

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Invalid section type for")
            elements: list = parser.parse(html)

        tree: sp.SemanticTree = sp.TreeBuilder().build(elements)
        items = ItemExtractor.extract_items(elements=elements, item_codes=item_codes)
        return items

    @staticmethod
    def get_summary(html: str) -> str:
        def split_text(text, max_length=512):
            """
            Splits text into chunks with a maximum token length to avoid exceeding model limits.
            """
            sentences = text.split(". ")
            chunks = []
            current_chunk = []
            current_length = 0

            for sentence in sentences:
                sentence_length = len(sentence.split())
                if current_length + sentence_length <= max_length:
                    current_chunk.append(sentence)
                    current_length += sentence_length
                else:
                    chunks.append(". ".join(current_chunk))
                    current_chunk = [sentence]
                    current_length = sentence_length

            if current_chunk:
                chunks.append(". ".join(current_chunk))

            return chunks

        summary = ""
        items = SEC_Filing_Parser.parse_filing_via_lib(html)
        if items:
            # Step 1: Extract and clean summaries
            summaries = []
            for item in items:
                for summary_text in item.summary:
                    cleaned_summary = (
                        summary_text.strip()
                    )  # Remove leading/trailing spaces or newlines
                    if (
                        cleaned_summary and cleaned_summary not in summaries
                    ):  # Avoid duplicates
                        summaries.append(cleaned_summary)

            # Join summaries into a single text blob
            full_text = "\n\n".join(summaries)

            # Step 2: Split the text into manageable chunks
            chunks = split_text(full_text, max_length=512)

            # Step 3: Initialize the summarization model
            summarizer = pipeline("summarization", model="t5-small", device=-1)

            # Step 4: Summarize each chunk
            chunk_summaries = []
            for chunk in chunks:
                compressed_summary = summarizer(
                    chunk, max_length=150, min_length=50, do_sample=False
                )
                chunk_summaries.append(compressed_summary[0]["summary_text"])
                logging.info(
                    f"Compressed original chunk : {chunk} to \n \n [Compressed] {compressed_summary[0]['summary_text']}"
                )
            # Step 5: Combine all chunk summaries into the final summary
            summary = " ".join(chunk_summaries)

        return summary
