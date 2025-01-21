"""
MongoDB database initialization
"""

from config import mongosettings
from pymongo import MongoClient
from pymongo.collection import Collection


client = MongoClient(mongosettings.uri)
db = client[mongosettings.database_name]


def init_collections():

    collections = db.list_collection_names()

    # Initialize public_entity collection
    if mongosettings.entities_coll_name not in db.list_collection_names():
        db.create_collection(mongosettings.entities_coll_name)
    # Initialize sec_filing_metadata collection
    if mongosettings.filing_metadatas_coll_name not in db.list_collection_names():
        db.create_collection(mongosettings.filing_metadatas_coll_name)
    # Initialize 8k-filings collection
    if mongosettings.filings_8k_coll_name not in db.list_collection_names():
        db.create_collection(mongosettings.filings_8k_coll_name)
    


# Initialize collections if they do not yet exist
init_collections()

# Export collections
public_entity_collection: Collection = db[mongosettings.entities_coll_name]
sec_filing_metadatas_collection: Collection = db[mongosettings.filing_metadatas_coll_name]
filings_8k_collection: Collection = db[mongosettings.filings_8k_coll_name]
btc_purchases_collection: Collection = db[mongosettings.btc_purchases_coll_name]
