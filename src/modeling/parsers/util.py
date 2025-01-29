from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

# Generic section of a filing


class Filing_Section_Generic(BaseModel):
    title: str
    content: str


# Generic parsed filing


class Parsed_Filing_Generic(BaseModel):
    sections: list[Filing_Section_Generic] = Field(default=[])

    def add_section(self, section: Filing_Section_Generic):
        self.sections.append(section)


class TOC_Supplement_Pages(str, Enum):
    S_1 = "S-1"
    S_2 = "S-2"
    S_3 = "S-3"
    S_4 = "S-4"
    S_5 = "S-5"
    S_6 = "S-6"
    S_7 = "S-7"
    S_8 = "S-8"
    S_9 = "S-9"
    S_10 = "S-10"


class TOC_Pages(str, Enum):
    P_1 = "1"
    P_2 = "2"
    P_3 = "3"
    P_4 = "4"
    P_5 = "5"
    P_6 = "6"
    P_7 = "7"
    P_8 = "8"
    P_9 = "9"
    P_10 = "10"


# Table of Content Element
class TOC_Element_Generic(BaseModel):
    item_str: Optional[str]
    title: str
    page_index: str
    href_link: str
    element_index_in_soup: int


class Table_Of_Content_Generic(BaseModel):
    elements: list[TOC_Element_Generic] = Field(default=[])

    def add_element(self, toc_element: TOC_Element_Generic):
        self.elements.append(toc_element)

    def is_empty(self):
        return len(self.rows) == 0


class Parsed_Filing_Generic_TOC(BaseModel):
    table_of_content: Table_Of_Content_Generic
    sections: list[Filing_Section_Generic] = Field(default=[])
