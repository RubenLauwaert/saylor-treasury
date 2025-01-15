from typing import List, Optional
from pydantic import BaseModel, Field, ValidationError
from modeling.sec_edgar.efts.EFTS_Response import EFTS_Response
from modeling.PublicEntity import PublicEntity
import requests
import logging


class EFTS_Request(BaseModel):
    base_url: str = Field(default="https://efts.sec.gov/LATEST/search-index")
    query: dict = Field(..., description="The query parameters to search for.")
    headers: dict = Field(
        default={"User-Agent": "Example company 2 - Contact: example@example.com"}
    )
    efts_response: Optional[EFTS_Response] = Field(
        None, description="The response from the Edgar Full Text Search."
    )

    def __init__(self, **data):
        super().__init__(**data)  # Let Pydantic handle validation and initialization

        # Automatically fetch and set the efts_response during initialization
        if self.query:
            first_response = requests.get(
                self.base_url, params=self.query, headers=self.headers
            )
            if first_response.status_code == 200:
                self.efts_response = EFTS_Response(**first_response.json())
            else:
                logging.error("Error:", first_response.status_code, first_response.text)
                self.efts_response = None
        else:
            logging.error("No query provided. Cannot fetch EFTS response.")
            self.efts_response = None

    @classmethod
    def from_query(cls, query: dict):
        """
        Helper method for initialization using only a query.
        """
        return cls(query=query)
    
    def get_entities(self) -> List[PublicEntity]:
        if self.efts_response is not None:
            return self.efts_response.get_entities()
        
