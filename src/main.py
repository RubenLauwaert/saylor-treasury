# FILE: main.py

import logging
import requests
from datetime import date
from modeling.efts.EFTS_Request import EFTS_Request
from modeling.PublicEntity import PublicEntity, PublicEntityType
from repositories import PublicEntityRepository
from database import public_entity_collection
from config import sec_edgar_settings

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Add entities to database
repository = PublicEntityRepository(public_entity_collection)


# Get entity by ticker
ticker = "MSTR"
entity = repository.get_entity_by_ticker(ticker)
cik = entity.cik if entity else None

# Get the formatted entity submissions URL
submissions_url = sec_edgar_settings.get_formatted_entity_submissions_url(cik)
company_facts_url = sec_edgar_settings.get_formatted_company_facts_url(cik)

# Define the headers with User-Agent
headers = {"User-Agent": "YourCompanyName - YourEmail@example.com"}

# Retrieve the content of the URLs
submissions_response = requests.get(submissions_url, headers=headers)
company_facts_response = requests.get(company_facts_url, headers=headers)

# Check if the requests were successful
if submissions_response.status_code == 200:
    submissions_data = submissions_response.json()
    logging.info(f"Submissions data: {submissions_data}")
else:
    logging.error(
        f"Failed to retrieve submissions data: {submissions_response.status_code}"
    )

if company_facts_response.status_code == 200:
    company_facts_data = company_facts_response.json()
    logging.info(f"Company facts data: {company_facts_data}")
else:
    logging.error(
        f"Failed to retrieve company facts data: {company_facts_response.status_code}"
    )

print(sec_edgar_settings.company_tickers_url)
