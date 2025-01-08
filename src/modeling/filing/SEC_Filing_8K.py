# FILE: SEC_Filing_8K.py

from pydantic import BaseModel, Field
from sec_downloader.types import FilingMetadata, CompanyAndAccessionNumber
from sec_downloader import Downloader
from config import sec_edgar_settings as ses


class SEC_Filing_8K(BaseModel):
    accession_number: str
    form_type: str
    primary_doc_url: str
    items: str
    primary_doc_description: str
    filing_date: str
    report_date: str
    cik: str
    company_name: str
    tickers: list
    content_html: bytes = Field(default=b"")

    @classmethod
    def from_metadata(cls, filing_metadata: FilingMetadata, include_html: bool = False):
        content_html = b""
        if include_html:
            # Initialize the downloader
            dl = Downloader(ses.sec_user_agent, ses.sec_user_agent_email)
            # Retrieve the content of the primary document URL
            try:
                filing_identifier = CompanyAndAccessionNumber(
                    ticker_or_cik=filing_metadata.cik,
                    accession_number=filing_metadata.accession_number,
                )
                content_html = dl.download_filing(filing_metadata.primary_doc_url)
            except Exception as e:
                print(f"Error retrieving HTML content: {e}")

        return cls(
            accession_number=filing_metadata.accession_number,
            form_type=filing_metadata.form_type,
            primary_doc_url=filing_metadata.primary_doc_url,
            items=filing_metadata.items,
            primary_doc_description=filing_metadata.primary_doc_description,
            filing_date=filing_metadata.filing_date,
            report_date=filing_metadata.report_date,
            cik=filing_metadata.cik,
            company_name=filing_metadata.company_name,
            tickers=filing_metadata.tickers,
            content_html=content_html,
        )
