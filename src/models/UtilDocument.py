from pydantic import BaseModel, Field
from datetime import datetime

class UtilDocument(BaseModel):
    id: str = Field(default="util_values", alias="_id", description="Unique identifier for the document", exclude=True)
    last_updated_db: datetime = Field(default=datetime.min, description="Timestamp of the last database update")
    last_synced_entities: datetime = Field(default=datetime.min, description="Timestamp of the last entity sync")

