from pydantic import BaseModel, Field
from typing import Optional
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
import logging
from sec_downloader import Downloader
from config import sec_edgar_settings as ses

class SEC_Filing(BaseModel):
    filing_metadata: SEC_Filing_Metadata = Field(description="Metadata of the given filing")
    content_html_str: Optional[str] = Field(default=None, description="Content of the filing")

    @classmethod
    def from_metadata(cls, filing_metadata: SEC_Filing_Metadata, include_content: bool = False):
        content_html_str = None    
        
        if include_content:
            try:
                dl = Downloader(ses.user_agent_header, ses.sec_user_agent_email)
                filing_url = filing_metadata.document_url
                content_html_str = dl.download_filing(url=filing_url).__str__()
                logging.info(f"Successfully retrieved content for URL: {filing_url}")
                logging.info(content_html_str)
            except Exception as e:
                logging.info(f"Error retrieving content from {filing_url}: {e}")
        
        return cls(filing_metadata=filing_metadata, content_html_str=content_html_str)