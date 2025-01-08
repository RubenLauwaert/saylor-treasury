# FILE: SEC_Downloader.py

from pydantic import BaseModel
from typing import List
from sec_downloader import Downloader
from sec_downloader.types import RequestedFilings, FilingMetadata
from modeling.util import ImportantDates
from modeling.filing.SEC_Filing_8K import SEC_Filing_8K
from config import sec_edgar_settings as ses
from datetime import date, datetime
import logging


class SEC_Downloader(BaseModel):

    def download_8k_filings(
        self,
        ticker_or_cik: str,
        after_date: date = ImportantDates.MSTR_GENESIS_DATE.value,
        include_content: bool = False,
    ) -> List[SEC_Filing_8K]:
        """Download 8-K filings for a given CIK."""

        # SEC downloader object
        dl = Downloader(ses.sec_user_agent, ses.sec_user_agent_email)
        # Get the 8-K filings
        requested_filings = RequestedFilings(
            ticker_or_cik=ticker_or_cik, form_type="8-K", limit=100
        )
        filing_metadatas = dl.get_filing_metadatas(requested_filings)

        # Filter out filings before the given after_date
        filtered_filings_metadatas = [
            filing
            for filing in filing_metadatas
            if datetime.strptime(filing.filing_date, "%Y-%m-%d").date() >= after_date
        ]

        filtered_filings = [
            SEC_Filing_8K.from_metadata(filing_metadata, include_html=include_content)
            for filing_metadata in filtered_filings_metadatas
        ]

        return filtered_filings
