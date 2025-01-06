from modeling.EFTS_Request import EFTS_Request
from modeling.PublicEntity import PublicEntity, PublicEntityType
from datetime import date
import json


# A more advanced keyword search can combine synonyms and forms:
base_bitcoin_8k_company_query = {
    "q": "(bitcoin OR Bitcoin) AND (FORM 8-K) AND NOT Trust ",
    "dateRange": "custom",
    "startdt": "2020-08-01",
    "enddt": date.today(),
}

# Bitcoin miners
base_bitcoin_8k_mining_company_query = {
    "q": "(bitcoin OR Bitcoin) AND (FORM 8-K) AND NOT Trust AND mining ",
    "dateRange": "custom",
    "startdt": "2024-12-15",
    "enddt": date.today(),
}
# Companies adding bitcoin to their balance sheet
base_bitcoin_balance_sheet_query = {
    "q": "(bitcoin OR Bitcoin) AND (purchase OR purchased OR acquire OR acquired OR added OR add)",
    "dateRange": "custom",
    "startdt": "2024-12-30",
    "enddt": date.today(),
}

efts_request = EFTS_Request(query=base_bitcoin_8k_company_query)
efts_response = efts_request.get_efts_response()
bitcoin_companies = []
for entity in efts_response.get_entities():

    if entity.entity_type == PublicEntityType.company:
        bitcoin_companies.append(
            {
                "name": entity.name,
                "cik": entity.cik,
                "ticker": entity.ticker,
                "entity_type": entity.entity_type,
            }
        )

print(json.dumps(bitcoin_companies, indent=4))
