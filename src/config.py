from pydantic_settings import BaseSettings
from pydantic import AliasChoices, MongoDsn, Field


class MongoSettings(BaseSettings):
    """Settings for the application."""

    uri: str = Field(validation_alias=AliasChoices("mongodb_uri", "mongodb_dsn"))

    database_name: str = Field(alias="mongodb_db_name")
    entities_coll_name: str = Field(validation_alias="mongodb_collection_entities")
    filings_coll_name: str = Field(validation_alias="mongodb_collection_8k_filings")
    btc_purchases_coll_name: str = Field(
        validation_alias="mongodb_collection_btc_purchases"
    )


mongosettings = MongoSettings()
