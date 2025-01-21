import logging
from pymongo.collection import Collection
from pymongo import UpdateOne, DeleteOne
from typing import List, Optional
from modeling.filing.SEC_Filing_Metadata import SEC_Filing_Metadata
from data_repositories.public_entity_repo import PublicEntity
from datetime import date
from logging import Logger


class SEC_Filing_Metadata_Repository:
    
    logger: Logger
    
    def __init__(self, collection: Collection):
        self.collection = collection
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_all_filing_metadatas(self) -> List[SEC_Filing_Metadata]:
        filings = self.collection.find()
        self.logger.info(
            f"Retrieved {self.collection.count_documents({})} filing metadatas from the collection."
        )
        return [SEC_Filing_Metadata(**filing) for filing in filings]

    def get_filing_metadata_by_id(self, filing_id: str) -> Optional[SEC_Filing_Metadata]:
        filing = self.collection.find_one({"_id": filing_id})
        if filing:
            self.logger.info(f"Found filing metadata with ID {filing_id}.")
            return SEC_Filing_Metadata(**filing)
        self.logger.warning(f"No filing metadata found with ID {filing_id}.")
        return None

    def get_filing_metadatas_for_entity(self, public_entity: PublicEntity) -> List[SEC_Filing_Metadata]:
        # Strip trailing zeros from the CIK
        company_cik = public_entity.cik
        ticker = public_entity.ticker
        filings = self.collection.find({"company_cik": company_cik}).sort("filing_date", -1)
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'company_cik': company_cik})} filing metadatas for entity with ticker {ticker}."
        )
        return [SEC_Filing_Metadata(**filing) for filing in filings]

    def get_filing_metadatas_for_entity_after_date(
        self, public_entity: PublicEntity, date: date
    ) -> List[SEC_Filing_Metadata]:
        cik = public_entity.cik
        ticker = public_entity.ticker
        date_str = date.isoformat()
        # Strip trailing zeros from the CIK
        filings = self.collection.find(
            {
                "company_cik": cik,
                "filing_date": {"$gt": date_str},
            }
        ).sort("filing_date", -1)
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'company_cik': cik, 'filing_date': {'$gt': date_str}})} filing metadatas for entity with ticker {ticker} after {date_str}."
        )
        return [SEC_Filing_Metadata(**filing) for filing in filings]

    def get_8k_filing_metadatas_for(self, public_entity: PublicEntity) -> List[SEC_Filing_Metadata]:
        company_cik = public_entity.cik
        ticker = public_entity.ticker
        filings = self.collection.find(
            {
                "company_cik": company_cik,
                "primary_doc_description": "8-K"
            }
        ).sort("filing_date", -1)
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'company_cik': company_cik, 'primary_doc_description': '8-K'})} 8-K filing metadatas for entity with ticker {ticker}."
        )
        return [SEC_Filing_Metadata(**filing) for filing in filings]

    def get_8k_filing_metadatas_for_after_date(
        self, public_entity: PublicEntity, date: date
    ) -> List[SEC_Filing_Metadata]:
        cik = public_entity.cik
        ticker = public_entity.ticker
        date_str = date.isoformat()
        filings = self.collection.find(
            {
                "company_cik": cik,
                "primary_doc_description": "8-K",
                "filing_date": {"$gt": date_str},
            }
        ).sort("filing_date", -1)
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'company_cik': cik, 'primary_doc_description': '8-K', 'filing_date': {'$gt': date_str}})} 8-K filing metadatas for company {ticker} after {date_str}."
        )
        return [SEC_Filing_Metadata(**filing) for filing in filings]

    def add_filing_metadata(self, filing_metadata: SEC_Filing_Metadata):
        self.collection.insert_one(filing_metadata.model_dump())
        self.logger.info(f"Added filing metadata with ID {filing_metadata.filing_id}.")

    def add_filing_metadatas(self, filing_metadatas: List[SEC_Filing_Metadata]):
        operations = [UpdateOne({"accession_number": fm.accession_number}, {"$set": fm.model_dump()}, upsert=True) for fm in filing_metadatas]
        if(len(operations) > 0):
            self.collection.bulk_write(operations)
            self.logger.info(f"Added or updated {len(filing_metadatas)} filing metadatas.")
        else:
            self.logger.info(f"No filing metadatas to add or update.")

    def update_filing_metadata(self, filing_metadata: SEC_Filing_Metadata):
        self.collection.update_one(
            {"_id": filing_metadata.filing_id},
            {"$set": filing_metadata.model_dump()},
            upsert=True
        )
        self.logger.info(f"Updated filing metadata with ID {filing_metadata.filing_id}.")

    def update_filing_metadatas(self, filing_metadatas: List[SEC_Filing_Metadata]):
        operations = [UpdateOne({"accession_number": fm.accession_number}, {"$set": fm.model_dump()}, upsert=True) for fm in filing_metadatas]
        self.collection.bulk_write(operations)
        self.logger.info(f"Updated {len(filing_metadatas)} filing metadatas.")

    def delete_filing_metadata(self, filing_id: str):
        self.collection.delete_one({"_id": filing_id})
        self.logger.info(f"Deleted filing metadata with ID {filing_id}.")

    def delete_filing_metadatas(self, filing_ids: List[str]):
        operations = [DeleteOne({"_id": fid}) for fid in filing_ids]
        self.collection.bulk_write(operations)
        self.logger.info(f"Deleted {len(filing_ids)} filing metadatas.")

    def get_latest_filing_metadata_date_for(self, public_entity: PublicEntity) -> Optional[date]:
        company_cik = public_entity.cik
        ticker = public_entity.ticker
        latest_filing = self.collection.find({"company_cik": company_cik}).sort("filing_date", -1)
        latest_filing_list = latest_filing.to_list(length=1)
        if len(latest_filing_list) > 0: 
            latest_date = latest_filing_list[0]["filing_date"]
            self.logger.info(f"Latest filing date for entity with ticker {ticker} is {latest_date}.")
            return date.fromisoformat(latest_date)
        self.logger.warning(f"No filings found for entity with ticker {ticker}. Returning minimal date.")
        return date.min