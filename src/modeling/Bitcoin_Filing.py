from pydantic import BaseModel
from enum import Enum
from typing import List
import sec_parser as sp
from sec_parser import SemanticTree, AbstractSemanticElement, TreeNode


class BitcoinFilingState(str, Enum):
    BOUGHT = "BOUGHT"  # They've purchased BTC
    PLANNING = "PLANNING"  # They plan or consider buying BTC
    REFERENCE_ONLY = "REFERENCE_ONLY"  # They just mention BTC in passing


class ItemCode(str, Enum):
    ITEM_101 = "Item 1.01"
    ITEM_701 = "Item 7.01"
    ITEM_801 = "Item 8.01"


class Item(BaseModel):
    code: ItemCode
    text: str


class Parsed_Bitcoin_Filing(BaseModel):
    state: BitcoinFilingState
    full_text: str
    relevant_items: List[Item] = []

    @classmethod
    def from_tree(cls, tree: SemanticTree):
        # This method would be used to parse the semantic tree and extract the relevant information
        # for the filing
        raise NotImplementedError("from_tree is not implemented yet.")


# Example usage:
example_filing = Parsed_Bitcoin_Filing(
    state=BitcoinFilingState.DRAFT,
    full_text="This is the full text of the 8-K filing...",
)

print(example_filing)
