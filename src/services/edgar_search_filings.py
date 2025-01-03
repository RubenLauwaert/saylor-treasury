import requests
from typing import List
from modeling.EFTS import EFTS_Response
from modeling.Company import PublicEntity, map_to_company
from datetime import date

def get_us_btc_companies() -> List[PublicEntity]:
  # Search parameters
  base_url = "https://efts.sec.gov/LATEST/search-index"
  query = {
      "q": "bitcoin",  # Keyword to search
      "dateRange": "custom",  # Specify a date range
      "startdt": "2009-08-01",  # Start date
      "enddt": date.today(),  # End date
      "form": "8-K"  # Form type
  }
  headers = {
      "User-Agent": "MyCompanyName - Contact: your_email@example.com"
  }

  # Send the search request
  response = requests.get(base_url, params=query, headers=headers)

  if response.status_code == 200:
      result = response.json()
      efts_response = EFTS_Response(**result)
      public_entities = [ PublicEntity.from_cik(hits.source.get_cik_number()) for hits in efts_response.hits.hits]
      return public_entities    
  else:
      print("Error:", response.status_code, response.text)
      
def get_foreign_btc_companies() -> List[PublicEntity]:
  # Search parameters
  base_url = "https://efts.sec.gov/LATEST/search-index"
  query = {
      "q": "bitcoin",  # Keyword to search
      "dateRange": "custom",  # Specify a date range
      "startdt": "2009-08-01",  # Start date
      "enddt": date.today(),  # End date
      "form": "6-K"  # Form type
  }
  headers = {
      "User-Agent": "MyCompanyName - Contact: your_email@example.com"
  }

  # Send the search request
  response = requests.get(base_url, params=query, headers=headers)

  if response.status_code == 200:
      result = response.json()
      efts_response = EFTS_Response(**result)
      # Use a dictionary to deduplicate by CIK
      unique_companies = {
          company.cik: company
          for hits in efts_response.hits.hits
          if (company := map_to_company(hits.source)) and company.cik
      }
      
      # Return the unique companies as a list
      return list(unique_companies.values())
  else:
      print("Error:", response.status_code, response.text)
      
      
