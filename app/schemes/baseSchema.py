from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class BaseOpportunitySchema(BaseModel):
    title: str
    description: str
    source_url: HttpUrl

    deadline: Optional[datetime] = None
    published_at: Optional[datetime] = None

    country: Optional[str] = None
    region: Optional[str] = None
    language: Optional[str] = None

    provider: str
    image_url: Optional[HttpUrl] = None  # если используете URL

    class Config:
        orm_mode = True

class BaseOpportunityUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[HttpUrl] = None

    deadline: Optional[datetime] = None
    published_at: Optional[datetime] = None

    country: Optional[str] = None
    region: Optional[str] = None
    language: Optional[str] = None

    provider: Optional[str] = None
    image_url: Optional[HttpUrl] = None
