from typing import Optional
from pydantic import BaseModel, Field
from modeling.sec_edgar.efts.EFTS_Response import EFTS_Response
import math
import requests


class EFTS_Request(BaseModel):
    base_url: str = Field(default="https://efts.sec.gov/LATEST/search-index")
    query: dict = Field(..., description="The query parameters to search for.")
    headers: dict = Field(
        default={"User-Agent": "Example company 2 - Contact: example@example.com"}
    )
    efts_response: Optional[EFTS_Response] = Field(
        None, description="The response from the Edgar Full Text Search."
    )

    def get_efts_response(self, max_pages: int = 100) -> Optional[EFTS_Response]:
        """
        Fetch all pages of results from the EDGAR Full Text Search API and merge them into a single EFTS_Response.
        :param max_pages: Optionally limit the number of pages to retrieve (useful if the total is very large).
        :return: An EFTS_Response containing hits from all pages.
        """

        all_hits = []
        current_page = 1

        first_response = requests.get(
            self.base_url, params=self.query, headers=self.headers
        )

        if first_response.status_code != 200:
            print("Error:", first_response.status_code, first_response.text)
            return None

        first_efts_response = EFTS_Response(**first_response.json())
        total_hits = first_efts_response.hits.total["value"]
        total_pages = min(total_hits / 100 + 1, max_pages)
        print("Number of hits to fetch is: ", total_hits)
        # Copy original query to avoid mutating self.query
        paginated_query = dict(self.query)

        while total_pages >= current_page:
            # Update the page parameter
            paginated_query["page"] = current_page

            response = requests.get(
                self.base_url, params=paginated_query, headers=self.headers
            )
            if response.status_code != 200:
                print("Error:", response.status_code, response.text)
                break

            data = response.json()

            # The chunk of hits on this page
            page_hits = data.get("hits", {}).get("hits", [])
            all_hits.extend(page_hits)

            print(
                f"Fetched page {current_page} with {len(page_hits)} hits (total so far: {len(all_hits)})."
            )

            # If we have fewer than 100 hits, it usually means we’re at the last page
            if len(page_hits) < 100:
                break

            # Respect a user-defined max_pages if provided
            if max_pages and current_page >= max_pages:
                print("Reached max_pages limit, stopping pagination.")
                break

            current_page += 1

        # If we have at least one page, let's merge everything into one final response
        if len(all_hits) > 0:
            # Use the last response `data` as our base, then overwrite hits
            data["hits"]["hits"] = all_hits

            try:
                self.efts_response = EFTS_Response(**data)
                return self.efts_response
            except Exception as e:
                print("Error building EFTS_Response:", e)

        return None

    @classmethod
    def from_query(cls, query: dict):
        return cls(query=query)
