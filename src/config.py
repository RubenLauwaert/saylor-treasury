from pydantic_settings import BaseSettings
from pydantic import AliasChoices, Field


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


class SECEdgarAPISettings(BaseSettings):
    """Settings for the public SEC Edgar API."""

    sec_user_agent: str = Field(alias="sec_user_agent")
    sec_user_agent_email: str = Field(alias="sec_user_agent_email")
    company_tickers_url: str = Field("https://www.sec.gov/files/company_tickers.json")
    base_company_facts_url: str = Field("https://data.sec.gov/api/xbrl/companyfacts/")
    base_entity_submissions_url: str = Field("https://data.sec.gov/submissions/")
    user_agent_header: dict = Field(
        {"User-Agent": f"{sec_user_agent} - ({sec_user_agent_email})"}
    )

    def get_formatted_company_facts_url(self, cik: str) -> str:
        return f"{self.base_company_facts_url}CIK{cik}.json"

    def get_formatted_entity_submissions_url(self, cik: str) -> str:
        return f"{self.base_entity_submissions_url}CIK{cik}.json"


sec_edgar_settings = SECEdgarAPISettings()
