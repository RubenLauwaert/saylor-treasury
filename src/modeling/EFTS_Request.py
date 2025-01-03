from typing import Optional
from pydantic import BaseModel, Field
from modeling.EFTS_Response import EFTS_Response
import requests

class EFTS_Request(BaseModel):
  base_url: str = Field(default="https://efts.sec.gov/LATEST/search-index")
  query: dict = Field(..., description="The query parameters to search for.")
  headers: dict = Field(default= { "User-Agent": "Example company - Contact:"})
  efts_response: Optional[EFTS_Response] = Field(None, description="The response from the Edgar Full Text Search.")
  
  def get_efts_response(self) -> EFTS_Response :
    response = requests.get(self.base_url, params=self.query, headers=self.headers)
    if response.status_code == 200:
      result = response.json()
      print(len(result['hits']['hits']))
      try:
        self.efts_response = EFTS_Response(**result)
        return self.efts_response
      except Exception as e:
        print("Error:", e)
    else:
      print("Error:", response.status_code, response.text)
  
  @classmethod
  def from_query(cls, query: dict):
    return cls(query=query)