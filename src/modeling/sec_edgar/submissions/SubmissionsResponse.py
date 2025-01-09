# FILE: src/modeling/sec_edgar/submissions/SubmissionsResponse.py

from pydantic import BaseModel, Field
from typing import List, Optional
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from config import sec_edgar_settings as ses
class SubmissionsResponse(BaseModel):
    cik: str
    entity_name: str
    filing_metadatas: List[SEC_Filing_Metadata]

    @classmethod
    def from_dict(cls, data: dict):
        recent_filings = data.get("filings", {}).get("recent", {})
        cik = data.get("cik", "").zfill(10)
        entity_name = data.get("entityName", "")
        filing_metadatas = [
            SEC_Filing_Metadata(
                document_url=ses.get_document_url(cik=cik, 
                                                  accession_number=recent_filings["accessionNumber"][i],
                                                  primary_document=recent_filings["primaryDocument"][i] ),
                company_cik=cik,
                accession_number=recent_filings["accessionNumber"][i].replace("-", ""),
                filing_date=recent_filings["filingDate"][i],
                report_date=recent_filings.get("reportDate", [None])[i] or None,
                acceptance_date_time=recent_filings["acceptanceDateTime"][i],
                act=recent_filings.get("act", [None])[i] or None,
                form=recent_filings["form"][i],
                file_number=recent_filings.get("fileNumber", [None])[i] or None,
                film_number=recent_filings.get("filmNumber", [None])[i] or None,
                items=(
                    recent_filings.get("items", [""])[i].split(",")
                    if recent_filings.get("items", [""])[i]
                    else None
                ),
                size=recent_filings.get("size", [None])[i],
                is_xbrl=recent_filings.get("isXBRL", [None])[i],
                is_inline_xbrl=recent_filings.get("isInlineXBRL", [None])[i],
                primary_document=recent_filings["primaryDocument"][i],
                primary_doc_description=recent_filings.get(
                    "primaryDocDescription", [None]
                )[i]
                or None,
            )
            for i in range(len(recent_filings["accessionNumber"]))
        ]
        return cls(
            cik=cik,
            entity_name=entity_name,
            filing_metadatas=filing_metadatas
        )
