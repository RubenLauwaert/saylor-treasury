import logging
from pymongo.collection import Collection
from pymongo import UpdateOne, DeleteOne
from typing import List, Optional
from modeling.filing.sec_8k.Filing_8K import Filing_8K
from modeling.PublicEntity import PublicEntity
from datetime import date
from logging import Logger


class SEC_Filing_8K_Repository:
    
    logger: Logger
    
    def __init__(self, collection: Collection):
        self.collection = collection
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_all_filings(self) -> List[Filing_8K]:
        filings = self.collection.find()
        self.logger.info(
            f"Retrieved {self.collection.count_documents({})} 8-K filings from the collection."
        )
        return [Filing_8K(**filing) for filing in filings]

    def get_filing_by_accession_number(self, accession_number: str) -> Optional[Filing_8K]:
        filing = self.collection.find_one({"filing_metadata.accession_number": accession_number})
        if filing:
            self.logger.info(f"Found 8-K filing with accession number {accession_number}.")
            return Filing_8K(**filing)
        self.logger.warning(f"No 8-K filing found with accession number {accession_number}.")
        return None

    def get_filings_for_entity(self, public_entity: PublicEntity) -> List[Filing_8K]:
        company_cik = public_entity.cik
        ticker = public_entity.ticker
        filings = self.collection.find({"filing_metadata.company_cik": company_cik}).sort("filing_metadata.filing_date", -1)
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'filing_metadata.company_cik': company_cik})} 8-K filings for {ticker}."
        )
        return [Filing_8K(**filing) for filing in filings]

    def get_filings_for_entity_after_date(
        self, public_entity: PublicEntity, date: date
    ) -> List[Filing_8K]:
        cik = public_entity.cik
        ticker = public_entity.ticker
        date_str = date.isoformat()
        filings = self.collection.find(
            {
                "filing_metadata.company_cik": cik,
                "filing_metadata.filing_date": {"$gt": date_str},
            }
        ).sort("filing_metadata.filing_date", -1)
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'filing_metadata.company_cik': cik, 'filing_metadata.filing_date': {'$gt': date_str}})} 8-K filings for {ticker} after {date_str}."
        )
        return [Filing_8K(**filing) for filing in filings]

    def add_filing(self, filing: Filing_8K):
        self.collection.insert_one(filing.model_dump())
        self.logger.info(f"Added 8-K filing with accession number {filing.filing_metadata.accession_number}.")

    def add_filings(self, filings: List[Filing_8K]):
        operations = [UpdateOne({"filing_metadata.accession_number": f.filing_metadata.accession_number}, {"$set": f.model_dump()}, upsert=True) for f in filings]
        if(len(operations) > 0):
            self.collection.bulk_write(operations)
            self.logger.info(f"Added or updated {len(filings)} 8-K filings.")
        else:
            self.logger.info(f"No filings to add or update.")

    def update_filing(self, filing: Filing_8K):
        self.collection.update_one(
            {"filing_metadata.accession_number": filing.filing_metadata.accession_number},
            {"$set": filing.model_dump()},
            upsert=True
        )
        self.logger.info(f"Updated 8-K filing with accession number {filing.filing_metadata.accession_number}.")

    def update_filings(self, filings: List[Filing_8K]):
        operations = [UpdateOne({"filing_metadata.accession_number": f.filing_metadata.accession_number}, {"$set": f.model_dump()}, upsert=True) for f in filings]
        if(len(operations) > 0):
            self.collection.bulk_write(operations)
            self.logger.info(f"Updated {len(filings)} 8-K filings.")
        else:
            self.logger.info(f"No filings to update.")

    def delete_filing(self, accession_number: str):
        self.collection.delete_one({"filing_metadata.accession_number": accession_number})
        self.logger.info(f"Deleted 8-K filing with accession number {accession_number}.")

    def delete_filings(self, accession_numbers: List[str]):
        operations = [DeleteOne({"filing_metadata.accession_number": an}) for an in accession_numbers]
        self.collection.bulk_write(operations)
        self.logger.info(f"Deleted {len(accession_numbers)} 8-K filings.")

    def get_latest_filing_date_for(self, public_entity: PublicEntity) -> Optional[date]:
        company_cik = public_entity.cik
        ticker = public_entity.ticker
        latest_filing = self.collection.find({"filing_metadata.company_cik": company_cik}).sort("filing_metadata.filing_date", -1).limit(1)
        if latest_filing.count() > 0:
            latest_date = latest_filing[0]["filing_metadata"]["filing_date"]
            self.logger.info(f"Latest filing date for {ticker} is {latest_date}.")
            return date.fromisoformat(latest_date)
        self.logger.warning(f"No filings found for {ticker}.")
        return None