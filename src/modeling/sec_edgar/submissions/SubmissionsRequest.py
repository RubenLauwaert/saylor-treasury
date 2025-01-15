# FILE: src/modeling/sec_edgar/submissions/SubmissionsRequest.py

from pydantic import BaseModel, Field
from modeling.sec_edgar.submissions.SubmissionsResponse import SubmissionsResponse
from config import sec_edgar_settings as ses
import requests


class SubmissionsRequest(BaseModel):
    url: str = Field(description="URL of the Edgar API submissions request")
    cik: str = Field(
        description="CIK number of the public entity to retrieve the submissions from"
    )
    resp_content: SubmissionsResponse = Field(
        description="Content of the Edgar API submissions response"
    )

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_cik(cls, cik: str):
        url_str = ses.get_formatted_entity_submissions_url(cik=cik)
        request_header = ses.user_agent_header
        # Make request
        response = requests.get(url=url_str, headers=request_header)

        if response.status_code == 200:
            result = response.json()
            submissions_response = SubmissionsResponse.from_dict(result)
            return cls(url=url_str, cik=cik, resp_content=submissions_response)
        else:
            # Handle the case where the request fails
            return cls(
                url=url_str,
                cik=cik,
                resp_content=SubmissionsResponse(cik=cik, entity_name="", filing_metadatas=[]),
            )
