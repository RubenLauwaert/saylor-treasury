# FILE: repositories.py

import logging
from pymongo.collection import Collection
from pymongo import InsertOne, UpdateOne, DeleteOne
from typing import List, Optional
from modeling.PublicEntity import PublicEntity
from logging import Logger

class PublicEntityRepository:
    
    logger: Logger
    
    def __init__(self, collection: Collection):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.collection = collection

    def get_all_entities(self) -> List[PublicEntity]:
        entities = self.collection.find()
        self.logger.info(
            f"Retrieved {self.collection.count_documents({})} entities from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]

    def get_entity_by_cik(self, cik: str) -> Optional[PublicEntity]:
        entity = self.collection.find_one({"cik": cik})
        if entity:
            self.logger.info(f"Found entity with CIK {cik}.")
            return PublicEntity(**entity)
        self.logger.warning(f"No entity found with CIK {cik}.")
        return None

    def get_entity_by_ticker(self, ticker: str) -> Optional[PublicEntity]:
        entity = self.collection.find_one({"ticker": ticker})
        if entity:
            self.logger.info(f"Found entity with ticker {ticker}.")
            return PublicEntity(**entity)
        self.logger.warning(f"No entity found with ticker {ticker}.")
        return None

    def add_entity(self, entity: PublicEntity) -> str:
        result = self.collection.update_one(
            {"cik": entity.cik}, {"$set": entity.model_dump()}, upsert=True
        )
        if result.upserted_id:
            self.logger.info(f"Added new entity with CIK {entity.cik}.")
            return str(result.upserted_id)
        self.logger.info(f"Updated existing entity with CIK {entity.cik}.")
        return str(result.matched_count)

    def add_entities(self, entities: List[PublicEntity]) -> List[str]:
        operations = [
            UpdateOne({"cik": entity.cik}, {"$set": entity.model_dump()}, upsert=True)
            for entity in entities
        ]
        result = self.collection.bulk_write(operations)
        self.logger.info(f"Added or updated {len(result.upserted_ids)} entities.")
        return [str(id) for id in result.upserted_ids]

    def update_entity(self, cik: str, entity: PublicEntity) -> bool:
        result = self.collection.update_one({"cik": cik}, {"$set": entity.model_dump()})
        if result.modified_count > 0:
            self.logger.info(f"Updated entity with CIK {cik}.")
            return True
        self.logger.warning(f"No entity found with CIK {cik} to update.")
        return False

    def update_entities(self, entities: List[PublicEntity]) -> int:
        operations = [
            UpdateOne({"cik": entity.cik}, {"$set": entity.model_dump()})
            for entity in entities
        ]
        result = self.collection.bulk_write(operations)
        self.logger.info(f"Updated {result.modified_count} entities.")
        return result.modified_count

    def delete_entity(self, cik: str) -> bool:
        result = self.collection.delete_one({"cik": cik})
        if result.deleted_count > 0:
            self.logger.info(f"Deleted entity with CIK {cik}.")
            return True
        self.logger.warning(f"No entity found with CIK {cik} to delete.")
        return False

    def delete_entities(self, ciks: List[str]) -> int:
        operations = [DeleteOne({"cik": cik}) for cik in ciks]
        result = self.collection.bulk_write(operations)
        self.logger.info(f"Deleted {result.deleted_count} entities.")
        return result.deleted_count
    
    def get_bitcoin_mining_entities(self) -> List[PublicEntity]:
        entities = self.collection.find({"sic": "6199", "ticker": {"$exists": True, "$ne": None}, "entity_type": "operating"})
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'sic': '6199', 'ticker': {'$exists': True, '$ne': None}})} Bitcoin mining entities with a ticker from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]
    
    
    def get_entities_by_type(self, entity_type: str) -> List[PublicEntity]:
        entities = self.collection.find({"entity_type": entity_type, "ticker": {"$exists": True, "$ne": None}})
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'entity_type': 'operating'})} operating entities from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]
    
    def get_entities_by_sic(self, sic_str: str) -> List[PublicEntity]:
        entities = self.collection.find({"sic": sic_str, "ticker": {"$exists": True, "$ne": None}})
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'sic': sic_str})} entities with SIC {sic_str} from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]
    
    def get_entities_w_existing_ticker(self) -> List[PublicEntity]:
        entities = self.collection.find({"ticker": {"$exists": True, "$ne": None}})
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'ticker': {'$exists': True, '$ne': None}})} entities with a ticker from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]
    
    
    def get_foreign_entities(self) -> List[PublicEntity]:
        entities = self.collection.find({
            "filing_metadatas": {"$elemMatch": {"form": "6-K"}},
            "filing_metadatas.form": {"$ne": "8-K"}
        })
        self.logger.info(
            f"Retrieved {self.collection.count_documents({'filing_metadatas': {'$elemMatch': {'form': '6-K'}}, 'filing_metadatas.form': {'$ne': '8-K'}})} foreign entities with form 6-K and no form 8-K from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]
