from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import date


class EFTS_Hit_Source(BaseModel):
  ciks: List[str] = Field(..., description="The CIKs of the company.")
  display_names: List[str] = Field(..., description="The display names of the company.")
  file_date: date = Field(..., description="The date the filing was filed.")
  form_type: str = Field(..., alias= "form", description="The form type of the filing.")
  
  def get_name(self):
    return self.display_names[0]
  
  def get_cik_number(self):
    return self.ciks[0]
  
class EFTS_Hit(BaseModel):
  index: str = Field(..., alias="_index", description="The index of the hit.")
  id: str = Field(..., alias="_id", description="The ID of the hit.")
  score: float = Field(..., alias="_score", description="The score of the hit.")
  source: EFTS_Hit_Source = Field(..., alias="_source", description="The source of the hit.")

class EFTS_Hits_Dict(BaseModel):
  total: dict = Field(..., description="The total number of hits.")
  max_score: float = Field(..., description="The maximum score of the hits.")
  hits: List[EFTS_Hit] = Field(..., description="The hits.")


class EFTS_Response(BaseModel):
  took: int = Field(..., description="The number of milliseconds it took to process the request.")
  timed_out: bool = Field(..., description="Whether the request timed out.")
  shards: Optional[Any] = Field(None, alias="_shards",description="The number of shards that were successful and failed.")
  hits: EFTS_Hits_Dict = Field(..., description="The Edgar Full Text Search results.")
  aggregations: Optional[dict] = Field(None, description="The aggregations of the search results.")
  query: Optional[dict] = Field(None, description="The query used to search.")
  

  
