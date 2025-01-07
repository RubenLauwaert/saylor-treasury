# FILE: repositories.py

import logging
from pymongo.collection import Collection
from pymongo import InsertOne, UpdateOne, DeleteOne
from typing import List, Optional
from modeling.PublicEntity import PublicEntity


class PublicEntityRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def get_all_entities(self) -> List[PublicEntity]:
        entities = self.collection.find()
        logging.info(
            f"Retrieved {self.collection.count_documents({})} entities from the collection."
        )
        return [PublicEntity(**entity) for entity in entities]

    def get_entity_by_cik(self, cik: str) -> Optional[PublicEntity]:
        entity = self.collection.find_one({"cik": cik})
        if entity:
            logging.info(f"Found entity with CIK {cik}.")
            return PublicEntity(**entity)
        logging.warning(f"No entity found with CIK {cik}.")
        return None

    def add_entity(self, entity: PublicEntity) -> str:
        result = self.collection.update_one(
            {"cik": entity.cik}, {"$set": entity.model_dump()}, upsert=True
        )
        if result.upserted_id:
            logging.info(f"Added new entity with CIK {entity.cik}.")
            return str(result.upserted_id)
        logging.info(f"Updated existing entity with CIK {entity.cik}.")
        return str(result.matched_count)

    def add_entities(self, entities: List[PublicEntity]) -> List[str]:
        operations = [
            UpdateOne({"cik": entity.cik}, {"$set": entity.model_dump()}, upsert=True)
            for entity in entities
        ]
        result = self.collection.bulk_write(operations)
        logging.info(f"Added or updated {len(result.upserted_ids)} entities.")
        return [str(id) for id in result.upserted_ids]

    def update_entity(self, cik: str, entity: PublicEntity) -> bool:
        result = self.collection.update_one({"cik": cik}, {"$set": entity.model_dump()})
        if result.modified_count > 0:
            logging.info(f"Updated entity with CIK {cik}.")
            return True
        logging.warning(f"No entity found with CIK {cik} to update.")
        return False

    def update_entities(self, entities: List[PublicEntity]) -> int:
        operations = [
            UpdateOne({"cik": entity.cik}, {"$set": entity.model_dump()})
            for entity in entities
        ]
        result = self.collection.bulk_write(operations)
        logging.info(f"Updated {result.modified_count} entities.")
        return result.modified_count

    def delete_entity(self, cik: str) -> bool:
        result = self.collection.delete_one({"cik": cik})
        if result.deleted_count > 0:
            logging.info(f"Deleted entity with CIK {cik}.")
            return True
        logging.warning(f"No entity found with CIK {cik} to delete.")
        return False

    def delete_entities(self, ciks: List[str]) -> int:
        operations = [DeleteOne({"cik": cik}) for cik in ciks]
        result = self.collection.bulk_write(operations)
        logging.info(f"Deleted {result.deleted_count} entities.")
        return result.deleted_count
