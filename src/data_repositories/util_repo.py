# FILE: repositories.py

import logging
from typing import Optional
from pymongo.collection import Collection
from pymongo import InsertOne, UpdateOne, DeleteOne
from database import util_collection
from logging import Logger
from datetime import datetime

from models.UtilDocument import UtilDocument

class UtilRepository:
    
    logger: Logger
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.collection = util_collection
        
        
    ### ✅ Fetch UtilDocument from MongoDB
    def get_util_document(self) -> Optional[UtilDocument]:
        doc = self.collection.find_one({"_id": "util_values"})  # Fetch by known ID
        if doc:
            self.logger.info("Fetched UtilDocument from database.")
            return UtilDocument(**doc)  # Convert MongoDB doc to Pydantic model
        self.logger.warning("UtilDocument not found in the database.")
        return None
      
      
 

    ### ✅ Getter for last_synced_entities
    def get_last_synced_entities(self) -> Optional[datetime]:
        result = self.collection.find_one({"_id": "util_values"}, {"last_synced_entities": 1, "_id": 0})
        if result and "last_synced_entities" in result:
            return result["last_synced_entities"]
        self.logger.warning("Could not retrieve last_synced_entities.")
        return None
      
      
    ### ✅ Getter for last_updated_db
    def get_last_updated_db(self) -> Optional[datetime]:
        result = self.collection.find_one({"_id": "util_values"}, {"last_updated_db": 1, "_id": 0})
        if result and "last_updated_db" in result:
            return result["last_updated_db"]
        self.logger.warning("Could not retrieve last_updated_db.")
        return None

    ### ✅ Update Last Synced Entities Timestamp
    def update_last_synced_entities(self, timestamp: datetime) -> bool:
        result = self.collection.update_one(
            {"_id": "util_values"},
            {"$set": {"last_synced_entities": timestamp}}
        )
        if result.modified_count > 0:
            self.logger.info(f"Updated last_synced_entities to {timestamp}.")
            return True
        self.logger.warning("Failed to update last_synced_entities.")
        return False

    ### ✅ Update Last Updated DB Timestamp
    def update_last_updated_db(self, timestamp: datetime) -> bool:
        result = self.collection.update_one(
            {"_id": "util_values"},
            {"$set": {"last_updated_db": timestamp}}
        )
        if result.modified_count > 0:
            self.logger.info(f"Updated last_updated_db to {timestamp}.")
            return True
        self.logger.warning("Failed to update last_updated_db.")
        return False

    ### ✅ Reset Timestamps to Default (0001-01-01T00:00:00)
    def reset_timestamps(self) -> bool:
        default_time = datetime.min  # 0001-01-01T00:00:00
        result = self.collection.update_one(
            {"_id": "util_values"},
            {"$set": {"last_updated_db": default_time, "last_synced_entities": default_time}}
        )
        if result.modified_count > 0:
            self.logger.info("Reset timestamps to default (0001-01-01T00:00:00).")
            return True
        self.logger.warning("Failed to reset timestamps.")
        return False

    ### ✅ Set Custom Field Value (Generic Method)
    def update_field(self, field_name: str, value) -> bool:
        """
        Update a single field dynamically.
        Example: update_field("cache_expiry", datetime.utcnow())
        """
        result = self.collection.update_one(
            {"_id": "util_values"},
            {"$set": {field_name: value}}
        )
        if result.modified_count > 0:
            self.logger.info(f"Updated {field_name} to {value}.")
            return True
        self.logger.warning(f"Failed to update {field_name}.")
        return False

    ### ✅ Create Default UtilDocument if Not Exists
    def ensure_util_document_exists(self) -> None:
        """Ensure the util document exists, otherwise insert the default one."""
        default_doc = UtilDocument().dict(by_alias=True)
        existing = self.collection.find_one({"_id": "util_values"})
        if not existing:
            self.collection.insert_one(default_doc)
            self.logger.info("Inserted default UtilDocument.")
        else:
            self.logger.info("UtilDocument already exists.")
      

