# FILE: main.py

import logging
from datetime import date
from modeling.efts.EFTS_Request import EFTS_Request
from modeling.PublicEntity import PublicEntity, PublicEntityType
from repositories import PublicEntityRepository
from database import public_entity_collection

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# A more advanced keyword search can combine synonyms and forms:
base_bitcoin_8k_company_query = {
    "q": "(bitcoin OR Bitcoin) AND (FORM 8-K)",
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

logging.info("Starting EFTS request for Bitcoin 8-K company query.")
efts_request = EFTS_Request(query=base_bitcoin_8k_company_query)
efts_response = efts_request.get_efts_response()
entities = efts_response.get_entities()

logging.info(f"Retrieved {len(entities)} entities from EFTS response.")

# Add entities to database
repository = PublicEntityRepository(public_entity_collection)
repository.add_entities(entities)

db_entities = repository.get_all_entities()
logging.info(f"Retrieved {len(db_entities)} entities from the database.")
print(db_entities)
