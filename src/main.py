from modeling.EFTS_Request import EFTS_Request
from datetime import date


base_bitcoin_8k_query = {
      "q": "bitcoin",  # Keyword to search
      "dateRange": "custom",  # Specify a date range
      "startdt": "2024-08-01",  # Start date
      "enddt": date.today(),  # End date
      "form": "8-K"  # Form type
  }

efts_request = EFTS_Request(query=base_bitcoin_8k_query)
efts_response = efts_request.get_efts_response()
hits = efts_response.hits.hits
print(efts_response.hits.total)
print(hits)  
for hit in hits:
    print(hit.source.form_type)