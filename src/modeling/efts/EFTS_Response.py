import requests
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import date

from modeling.PublicEntity import PublicEntity


class EFTS_Hit_Source(BaseModel):
    ciks: List[str] = Field(..., description="The CIKs of the company.")
    display_names: List[str] = Field(
        ..., description="The display names of the company."
    )
    file_date: date = Field(..., description="The date the filing was filed.")
    form_type: str = Field(
        ..., alias="form", description="The form type of the filing."
    )

    def get_name(self):
        return self.display_names[0]

    def get_cik_number(self):
        return self.ciks[0]


class EFTS_Hit(BaseModel):
    index: str = Field(..., alias="_index", description="The index of the hit.")
    id: str = Field(..., alias="_id", description="The ID of the hit.")
    score: float = Field(..., alias="_score", description="The score of the hit.")
    source: EFTS_Hit_Source = Field(
        ..., alias="_source", description="The source of the hit."
    )
    url: Optional[str] = Field(None, description="The URL of the SEC filing hit.")

    def get_source_name(self):
        return self.source.get_name()

    def get_source_cik(self):
        return self.source.get_cik_number()

    def get_file_date(self):
        return self.source.file_date

    def get_form_type(self):
        return self.source.form_type

    def get_url(self):
        base_url = "https://www.sec.gov/Archives/edgar/data"
        cik = self.get_source_cik()
        parts = self.id.split(":")
        if len(parts) == 2:
            accession_number, file_name = parts
            accession_number = accession_number.replace("-", "")
            return f"{base_url}/{cik}/{accession_number}/{file_name}"
        return None


class EFTS_Hits_Dict(BaseModel):
    total: dict = Field(..., description="The total number of hits.")
    max_score: Optional[float] = Field(
        None, description="The maximum score of the hits."
    )
    hits: List[EFTS_Hit] = Field(..., max_length=10000, description="The hits.")


class EFTS_Response(BaseModel):
    took: int = Field(
        ..., description="The number of milliseconds it took to process the request."
    )
    timed_out: bool = Field(..., description="Whether the request timed out.")
    shards: Optional[Any] = Field(
        None,
        alias="_shards",
        description="The number of shards that were successful and failed.",
    )
    hits: EFTS_Hits_Dict = Field(..., description="The Edgar Full Text Search results.")
    aggregations: Optional[dict] = Field(
        None, description="The aggregations of the search results."
    )
    query: Optional[dict] = Field(None, description="The query used to search.")

    def get_hits(self) -> List[EFTS_Hit]:
        # Ensure hits.hits exists and return it
        if self.hits and self.hits.hits:
            return self.hits.hits
        return []

    def get_entities(self) -> List[PublicEntity]:
        unique_entities = set()

        for hit in self.get_hits():
            display_name = hit.source.get_name()
            cik = hit.source.get_cik_number()
            unique_entities.add((display_name, cik))

        return [
            PublicEntity.map_to_entity(name, cik) for (name, cik) in unique_entities
        ]
