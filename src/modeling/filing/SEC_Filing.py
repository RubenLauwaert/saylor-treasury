from pydantic import BaseModel, Field
from typing import Optional
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from modeling.parsers.SECFilingParser import *
import logging
from sec_downloader import Downloader
from config import sec_edgar_settings as ses

class SEC_Filing(BaseModel):
    filing_metadata: SEC_Filing_Metadata = Field(description="Metadata of the given filing")
    content_html_str: Optional[str] = Field(default=None, description="Content of the filing")
    is_parsed: bool = Field(default=False, description="Whether the content has been parsed")
    has_raw_content: bool = Field(default=False, description="Whether the content has been retrieved")
    items: Optional[List[Item]] = Field(default=[], description="Items extracted from the filing")

    @classmethod
    def from_metadata(cls, filing_metadata: SEC_Filing_Metadata, include_content: bool = False):
        content_html_str = None    
        items = []
        is_parsed = False
        has_raw_content = False
        if include_content:
            try:
                # Retrieve raw html content
                dl = Downloader(ses.user_agent_header, ses.sec_user_agent_email)
                filing_url = filing_metadata.document_url
                content_html_str = dl.download_filing(url=filing_url).__str__()
                has_raw_content = True
                logging.info(f"Successfully retrieved content for URL: {filing_url}")
                # Parse raw html content into list of items
                items = SEC_Filing_Parser.parse_filing_via_lib(content_html_str, filing_metadata.items)
                is_parsed = True
                logging.info(f"Successfully parsed content for URL: {filing_url}")
            except Exception as e:
                logging.info(f"Error retrieving content from {filing_url}: {e}")
        
        return cls(filing_metadata=filing_metadata, 
                   content_html_str=content_html_str, 
                   items=items,
                   is_parsed=is_parsed,
                   has_raw_content=has_raw_content)