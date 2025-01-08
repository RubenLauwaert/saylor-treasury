# FILE: src/modeling/sec_edgar/submissions/SubmissionsResponse.py

from pydantic import BaseModel, Field
from typing import List, Optional


class Filing(BaseModel):
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


class SubmissionsResponse(BaseModel):
    cik: str
    entity_name: str
    filings: List[Filing]

    @classmethod
    def from_dict(cls, data: dict):
        recent_filings = data.get("filings", {}).get("recent", {})
        filings = [
            Filing(
                accession_number=recent_filings["accessionNumber"][i],
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
            cik=data.get("cik", ""),
            entity_name=data.get("entityName", ""),
            filings=filings,
        )
