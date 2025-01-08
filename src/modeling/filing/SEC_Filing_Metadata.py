from pydantic import BaseModel
from typing import List, Optional


class SEC_Filing_Metadata(BaseModel):
    document_url: Optional[str]
    accession_number: str
    filing_date: str
    report_date: Optional[str]
    acceptance_date_time: str
    act: Optional[str]
    form: str
    file_number: Optional[str]
    film_number: Optional[str]
    items: Optional[List[str]]
    size: Optional[int]
    is_xbrl: Optional[bool]
    is_inline_xbrl: Optional[bool]
    primary_document: str
    primary_doc_description: Optional[str]
    
    