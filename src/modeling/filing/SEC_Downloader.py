# FILE: SEC_Downloader.py

from pydantic import BaseModel
from typing import List
from sec_downloader import Downloader
from sec_downloader.types import RequestedFilings, FilingMetadata
from modeling.util import ImportantDates
from config import sec_edgar_settings as ses
from datetime import date, datetime
import logging


class SEC_Downloader(BaseModel):

    def download_8k_filing_metadatas(
        self, cik: str, after_date: date = ImportantDates.MSTR_GENESIS_DATE.value
    ) -> List[FilingMetadata]:
        """Download 8-K filings for a given CIK."""

        # SEC downloader object
        dl = Downloader(ses.sec_user_agent, ses.sec_user_agent_email)
        # Get the 8-K filings
        requested_filings = RequestedFilings(
            ticker_or_cik=cik, form_type="8-K", limit=100
        )
        filing_metadatas = dl.get_filing_metadatas(requested_filings)

        # Filter out filings before the given after_date
        filtered_filings = [
            filing
            for filing in filing_metadatas
            if datetime.strptime(filing.filing_date, "%Y-%m-%d").date() >= after_date
        ]

        return filtered_filings
