import logging
from pymongo.collection import Collection
from pymongo import UpdateOne, DeleteOne
from typing import List, Optional
from modeling.filing.SEC_Filing import SEC_Filing
from data_repositories.public_entity_repo import PublicEntity
from datetime import date


class SEC_FilingRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def get_all_filings(self) -> List[SEC_Filing]:
        filings = self.collection.find()
        logging.info(
            f"Retrieved {self.collection.count_documents({})} filings from the collection."
        )
        return [SEC_Filing(**filing) for filing in filings]

    def get_filing_by_id(self, filing_id: str) -> Optional[SEC_Filing]:
        filing = self.collection.find_one({"_id": filing_id})
        if filing:
            logging.info(f"Found filing with ID {filing_id}.")
            return SEC_Filing(**filing)
        logging.warning(f"No filing found with ID {filing_id}.")
        return None

    def get_filings_for_entity(self, public_entity: PublicEntity) -> List[SEC_Filing]:
        # Strip trailing zeros from the CIK
        company_cik = public_entity.cik
        filings = self.collection.find({"filing_metadata.company_cik": company_cik})
        logging.info(
            f"Retrieved {self.collection.count_documents({'filing_metadata.company_cik': company_cik})} filings for company CIK {company_cik}."
        )
        return [SEC_Filing(**filing) for filing in filings]

    def get_filings_for_entity_after_date(
        self, public_entity: PublicEntity, date: date
    ) -> List[SEC_Filing]:
        cik = public_entity.cik
        date_str = date.isoformat()
        # Strip trailing zeros from the CIK
        filings = self.collection.find(
            {
                "filing_metadata.company_cik": cik,
                "filing_metadata.filing_date": {"$gt": date_str},
            }
        )
        logging.info(
            f"Retrieved {self.collection.count_documents({'filing_metadata.company_cik': cik, 'filing_metadata.filing_date': {'$gt': date_str}})} filings for company CIK {cik} after {date_str}."
        )
        return [SEC_Filing(**filing) for filing in filings]

    def add_filing(self, filing: SEC_Filing) -> Optional[str]:
        existing_filing = self.collection.find_one(
            {
                "filing_metadata.accession_number": filing.filing_metadata.accession_number
            }
        )
        if existing_filing:
            logging.info(
                f"Filing with accession number {filing.filing_metadata.accession_number} already exists. Skipping insertion."
            )
            return None

        result = self.collection.insert_one(filing.model_dump())
        logging.info(
            f"Added new filing with accession number {filing.filing_metadata.accession_number}."
        )
        return str(result.inserted_id)

    def add_filings(self, filings: List[SEC_Filing]) -> List[str]:
        accession_numbers = [
            filing.filing_metadata.accession_number for filing in filings
        ]
        existing_filings = self.collection.find(
            {"filing_metadata.accession_number": {"$in": accession_numbers}}
        )
        existing_accession_numbers = {
            filing["filing_metadata"]["accession_number"] for filing in existing_filings
        }

        new_filings = [
            filing.model_dump()
            for filing in filings
            if filing.filing_metadata.accession_number not in existing_accession_numbers
        ]

        if new_filings:
            result = self.collection.insert_many(new_filings)
            logging.info(f"Added {len(result.inserted_ids)} new filings.")
            return [str(inserted_id) for inserted_id in result.inserted_ids]
        else:
            logging.info("No new filings were added.")
            return []

    def update_filing(self, accession_number: str, filing: SEC_Filing) -> bool:
        result = self.collection.update_one(
            {"filing_metadata.accession_number": accession_number},
            {"$set": filing.model_dump()},
        )
        if result.modified_count > 0:
            logging.info(f"Updated filing with accession number {accession_number}.")
            return True
        logging.warning(
            f"No filing found with accession number {accession_number} to update."
        )
        return False

    def update_filings(self, filings: List[SEC_Filing]) -> int:
        operations = [
            UpdateOne(
                {
                    "filing_metadata.accession_number": filing.filing_metadata.accession_number
                },
                {"$set": filing.model_dump()},
            )
            for filing in filings
        ]
        result = self.collection.bulk_write(operations)
        logging.info(f"Updated {result.modified_count} filings.")
        return result.modified_count

    def delete_filing(self, accession_number: str) -> bool:
        result = self.collection.delete_one(
            {"filing_metadata.accession_number": accession_number}
        )
        if result.deleted_count > 0:
            logging.info(f"Deleted filing with accession number {accession_number}.")
            return True
        logging.warning(
            f"No filing found with accession number {accession_number} to delete."
        )
        return False

    def delete_filings(self, accession_numbers: List[str]) -> int:
        operations = [
            DeleteOne({"filing_metadata.accession_number": accession_number})
            for accession_number in accession_numbers
        ]
        result = self.collection.bulk_write(operations)
        logging.info(f"Deleted {result.deleted_count} filings.")
        return result.deleted_count
