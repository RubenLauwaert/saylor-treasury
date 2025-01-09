from bs4 import BeautifulSoup
from typing import List, Optional
from pydantic import BaseModel

class TreeNode(BaseModel):
    tag: str
    text: str
    children: List["TreeNode"] = []

class SemanticTree(BaseModel):
    root: TreeNode

    @classmethod
    def from_html(cls, html: str) -> "SemanticTree":
        soup = BeautifulSoup(html, 'html.parser')
        root = cls._parse_element(soup)
        return cls(root=root)

    @classmethod
    def _parse_element(cls, element) -> TreeNode:
        node = TreeNode(tag=element.name, text=element.get_text(strip=True))
        for child in element.children:
            if child.name:  # Only consider tags, not strings
                node.children.append(cls._parse_element(child))
        return node

class ItemExtractor(BaseModel):
    @staticmethod
    def extract_items(tree: SemanticTree) -> List[str]:
        items = []
        for node in tree.root.children:
            if "item" in node.tag.lower():
                items.append(node.text)
        return items