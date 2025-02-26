"""
MongoDB database initialization
"""

from config import mongosettings
from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime, timezone

from models.UtilDocument import UtilDocument

client = MongoClient(mongosettings.uri)
db = client[mongosettings.database_name]


def init_collections():

    collections = db.list_collection_names()

    # Initialize public_entity collection
    if mongosettings.entities_coll_name not in db.list_collection_names():
        db.create_collection(mongosettings.entities_coll_name)
    # Initialize util collection
    if mongosettings.util_coll_name not in db.list_collection_names():
        db.create_collection(mongosettings.util_coll_name)
    
    
    # Ensure a single document exists in util_collection
    util_collection = db[mongosettings.util_coll_name]
    

    # Use upsert to insert the document only if it doesn't already exist
    util_collection.update_one(
        {"_id": "util_values"},
        {"$setOnInsert": UtilDocument().model_dump()},
        upsert=True
    )


# Initialize collections if they do not yet exist
init_collections()

# Export collections
public_entity_collection: Collection = db[mongosettings.entities_coll_name]
util_collection: Collection = db[mongosettings.util_coll_name]
