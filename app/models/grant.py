from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from typing import Optional
from datetime import datetime

class Grant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    source_url: str
    deadline: Optional[datetime] = None
    published_at: Optional[datetime] = None
    country: Optional[str] = None
    region: Optional[str] = None
    language: Optional[str] = None
    provider: str
    image_url: Optional[str] = None
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    def __repr__(self):
        return f"<GRANT {self.title}>"