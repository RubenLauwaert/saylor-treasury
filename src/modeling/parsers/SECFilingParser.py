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


class Item(BaseModel):
    code: Optional[ItemCode]
    subtitles: List[str]
    summary: List[str]

    class Config:
        use_enum_values = True


class ItemExtractor(BaseModel):

    @staticmethod
    def extract_items(tree: SemanticTree) -> List[Item]:
        items = []
        for node in tree.nodes:
            ItemExtractor._extract_items_recursive(node, items)

        if len(items) == 0:
            for node in tree.nodes:
                ItemExtractor._extract_items_recursive(
                    node, items, extensive_search=True
                )
        return items

    @staticmethod
    def _extract_items_recursive(
        node: TreeNode, items: List[Item], extensive_search: bool = False
    ):

        def extract_item_code(text: str) -> Optional[ItemCode]:
            match = re.search(r"Item\s*(\d+\.\d+)", text, re.IGNORECASE)
            if match:
                item_code_str = match.group(1).replace(".", "_")
                item_code_enum = f"ITEM_{item_code_str}"
                if item_code_enum in ItemCode.__members__:
                    return ItemCode[item_code_enum]
            return None

        semantic_element = node.semantic_element
        class_name = semantic_element.__class__.__name__
        logging.info(
            f"Processing {class_name} [{semantic_element.html_tag.name}] : {semantic_element.text}"
        )
        # Check for Item codes in Titles
        if isinstance(
            semantic_element, (TopSectionTitle, TitleElement, IrrelevantElement)
        ):
            if "item" in semantic_element.text.lower():
                item_code = extract_item_code(semantic_element.text)
                if item_code not in [item.code for item in items]:
                    item_text = ItemExtractor._extract_item_text(node)
                    # Item subtitles
                    item_subtitles = [
                        child.semantic_element.text
                        for child in node.children
                        if isinstance(child.semantic_element, TitleElement)
                    ]
                    items.append(
                        Item(
                            code=item_code, summary=item_text, subtitles=item_subtitles
                        )
                    )

        # # Check for Item codes in Text Elements
        # if True:
        #     if isinstance(semantic_element, (TextElement)):
        #         item_code = extract_item_code(semantic_element.text)
        #         # if item_code and not any(item.code == item_code for item in items):
        #             # Check whether the item code is already in the list
        #         items.append(Item(code=item_code, summary=[semantic_element.text[:2000]], subtitles=[]))

        if node.has_child:
            for child in node.children:
                ItemExtractor._extract_items_recursive(child, items)

    @staticmethod
    def _extract_item_text(node: TreeNode) -> List[str]:
        text_elements: List[str] = []
        for child in node.children:
            ItemExtractor._extract_item_text_rec(child, text_elements)

        return text_elements

    @staticmethod
    def _extract_item_text_rec(node: TreeNode, text_elements: List[str]):
        semantic_element = node.semantic_element

        if isinstance(semantic_element, (TextElement)):
            text_elements.append(semantic_element.text)

        if node.has_child:
            for child in node.children:
                ItemExtractor._extract_item_text_rec(child, text_elements)


class SEC_Filing_Parser(BaseModel):
    @staticmethod
    def parse_filing(html: str) -> Optional[List[str]]:
        tree = SemanticTree.from_html(html)
        print(f"Parsed Tree: {tree}")
        return ItemExtractor.extract_items(tree)

    @staticmethod
    def parse_filing_via_lib(html: str) -> Optional[List[Item]]:

        parser = sp.Edgar10QParser()

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Invalid section type for")
            elements: list = parser.parse(html)

        tree: sp.SemanticTree = sp.TreeBuilder().build(elements)
        items = ItemExtractor.extract_items(tree)
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
