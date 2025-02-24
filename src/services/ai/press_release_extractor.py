from logging import Logger
import logging
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from config import openai_settings
from datetime import datetime
from openai import AsyncOpenAI

class PressReleaseSummary(BaseModel):
    title: str = Field(..., description="Title of the press release")
    date: str = Field(..., description="Date of the press release in YYYY-MM-DD format")
    summary: str = Field(..., description="Brief summary of the press release content")
    url: str = Field(..., description="The url you used to extract the press release")
    
    @model_validator(mode='before')
    def check_values(cls, values):
      date = values.get('date')
      url = values.get('url')
      
      # Check if the date is in ISO format
      try:
        datetime.fromisoformat(date)
      except ValueError:
        raise ValueError(f"Date '{date}' is not in valid ISO format (YYYY-MM-DD).")
      
      return values
  

class PressReleaseExtraction(BaseModel):
    steps: List[str] = Field(..., description="The steps taken by the AI to extract the press release summaries")
    press_release_summaries: List[PressReleaseSummary]
    
class CompanyPressReleaseURL(BaseModel):
    company_name: str = Field(..., description="Full name of the company")
    ticker: str = Field(..., description="Stock ticker symbol")
    press_release_url: Optional[str] = Field(None, description="Root URL of the press release page")
    
class PressReleaseURLExtraction(BaseModel):
    results: List[CompanyPressReleaseURL]

class PressReleaseExtractor:
  
    client: AsyncOpenAI
    structured_output_model: str
    logger: Logger

    system_prompt = "You are an AI assistant that is used to transform extracted events from an SEC Filing into structured data. \
        Avoid guessing or making assumptions. Only use the information provided in the events to build the structured output."
  
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        try:
            self.client = openai_settings.get_async_client()
            self.logger.info(
                "AsyncOpenAI client initialized for Bitcoin Updates Extractor"
            )
            self.structured_output_model = openai_settings.structured_output_model
            self.logger.info(
                f"Using structured output model: {self.structured_output_model}"
            )

        except Exception as e:
            self.logger.error(f"Error initializing OpenAI API: {e}")
   

    def fetch_raw_press_releases(self, company_ticker: str) -> List[dict]:
        """Fetch raw press releases from an external source (to be implemented)."""
        # Placeholder: Fetch press releases from a web API or scraping tool
        # Example structure: [{"title": "...", "date": "YYYY-MM-DD", "content": "...", "url": "..."}]
        return []
    
    async def extract_press_release_summaries(self, company_ticker: str) -> List[PressReleaseSummary]:
        """Extract structured summaries for a given company ticker."""
          
        prompt_text = f"""Can you find me and summarize the five latest press releases for the public US company with ticker: {company_ticker}:
   
        
        Return the response as the requested structured output."""
        
        response = await self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial data assistant helping to extract press release summaries."},
                {"role": "user", "content": prompt_text}
            ],
            response_format=PressReleaseExtraction
        )
        
        # Extract the structured output from the response
        result = response.choices[0].message.parsed
        return result
    


    async def get_press_release_urls(self, company_tickers: List[str]) -> List[CompanyPressReleaseURL]:
        """Uses OpenAI to find press release URLs for multiple companies."""

        
        # Construct the prompt
        prompt_text = f"""
        Find the official press release URLs for the following companies with tickers : {company_tickers}.
        Return a JSON list with fields: company_name, ticker, press_release_url.
        """
        
        response = await self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI assistant that finds press release URLs for companies."},
                {"role": "user", "content": prompt_text}
            ],
            response_format=PressReleaseURLExtraction
        )
        
        # Extract the structured output from the response
        result = response.choices[0].message.parsed
        return result


