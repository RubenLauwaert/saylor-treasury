from openai import OpenAI, AsyncOpenAI
from pydantic_settings import BaseSettings
from pydantic import AliasChoices, Field, BaseModel

from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


# Configuration of MongoDB database
class MongoSettings(BaseSettings):
    """Settings for the application."""

    uri: str = Field(validation_alias=AliasChoices("mongodb_uri", "mongodb_dsn"))
    database_name: str = Field(alias="mongodb_db_name")
    entities_coll_name: str = Field(validation_alias="mongodb_collection_entities")
    util_coll_name: str = Field(validation_alias="MONGODB_COLLECTION_UTIL")


mongosettings = MongoSettings()


# Configuration of SEC Edgar API
class SECEdgarAPISettings(BaseSettings):
    """Settings for the public SEC Edgar API."""

    sec_user_agent: str = Field(alias="sec_user_agent")
    sec_user_agent_email: str = Field(alias="sec_user_agent_email")
    company_tickers_url: str = Field("https://www.sec.gov/files/company_tickers.json")
    base_company_facts_url: str = Field("https://data.sec.gov/api/xbrl/companyfacts/")
    base_entity_submissions_url: str = Field("https://data.sec.gov/submissions/")
    base_efts_url: str = Field("https://efts.sec.gov/LATEST/search-index")

    @property
    def user_agent_header(self) -> dict:
        """Generate the User-Agent header as a static string."""
        return {"User-Agent": f"{self.sec_user_agent} ({self.sec_user_agent_email})"}

    def get_formatted_company_facts_url(self, cik: str) -> str:
        return f"{self.base_company_facts_url}CIK{cik}.json"

    def get_formatted_entity_submissions_url(self, cik: str) -> str:
        return f"{self.base_entity_submissions_url}CIK{cik}.json"

    def get_document_url(
        self, cik: str, accession_number: str, primary_document: str
    ) -> str:
        accession_number = accession_number.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{primary_document}"


sec_edgar_settings = SECEdgarAPISettings()


# Configuration of OpenAI API Settings


class OpenAI_Settings(BaseSettings):
    """Settings for the OpenAI API."""

    api_key: str = Field(alias="openai_api_key")
    summarization_model: str = Field(alias="openai_summarization_model")
    structured_output_model: str = Field(alias="openai_structured_output_model")
    tokens_per_minute: int = Field(alias="OPENAI_TOKEN_LIMIT_TPM")
    tokens_per_day: int = Field(alias="OPENAI_TOKEN_LIMIT_TPD")
    requests_per_minute: int = Field(alias="OPENAI_TOKEN_LIMIT_RPM")
    tokens_per_request: int = Field(alias="OPENAI_TOKENS_PER_REQUEST")

    def get_client(self):
        return OpenAI(api_key=self.api_key)

    def get_async_client(self):
        return AsyncOpenAI(api_key=self.api_key)


openai_settings = OpenAI_Settings()
