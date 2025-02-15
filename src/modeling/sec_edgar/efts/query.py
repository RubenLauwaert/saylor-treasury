from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import date







class Base_EFTS_Query(BaseModel):
    q: str = Field(..., description="The query string.")
    startdt: str = Field(..., description="The start date for the query.")
    enddt: str = Field(..., description="The end date for the query.")
    ciks: Optional[str] = Field(None, description="The CIKs to search for.")
    forms: Optional[List[str]] = Field(None, description="The forms to search for.")
    category: Optional[str] = Field(None, description="The category to search for.")
    dateRange: Optional[str] = Field(None, description="The date range to search for.")
    from_: Optional[int] = Field(None, alias="from", description="The starting index for the search.")
    page: Optional[int] = Field(None, description="The page number for the search.")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class Base_Bitcoin_Query(Base_EFTS_Query):
    q: str = Field("bitcoin", description="The query string.")
    startdt: str = Field(default=date(2009, 1, 3).isoformat(), description="The start date for the query.")
    enddt: str = Field(default=date.today().isoformat(), description="The end date for the query.")
    forms: List[str] = Field(["8-K","10-Q","10-K"], description="The forms to search for.")
    
    
class QueryHit(BaseModel):
    url: str = Field(..., description="The filing url of the query hit")
    score: float = Field(..., description="The score of the hit.")
    accession_number: str = Field(..., description="The accession number of the filing.")
    file_type: str = Field(..., description="The type of the filing.")
    form_type: str = Field(..., description="The form type of the filing.")
    file_date: str = Field(..., description="The date the filing was filed.")
    cik: str = Field(..., description="The CIK of the company.")
    
    
class QueryResult(BaseModel):
    query : dict = Field(..., description="The query used to get the results.")
    hits: List[QueryHit] = Field(..., description="The hits from the query.")
    
    def get_entity_ciks(self):
        return set([hit.cik for hit in self.hits])
    
class QueryResults(BaseModel):
    results : List[QueryResult] = Field(..., description="The results from the queries.")
    
    def get_entity_ciks(self):
        ciks = set()
        for result in self.results:
            ciks.update(result.get_entity_ciks())
        return ciks