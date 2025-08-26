from sqlmodel import SQLModel, Field, Column
from typing import Optional
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime

class Scholarship(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    level: Optional[str] = None  # bachelor, master, phd

    title: str
    description: str
    source_url: str

    deadline: Optional[datetime] = None
    # НОВОЕ: исходный текст дедлайна (если он "December, 31 and June, 30 each year" и т.п.)
    deadline_text: Optional[str] = Field(default=None, sa_column=Column(pg.TEXT, nullable=True))

    published_at: Optional[datetime] = None

    country: Optional[str] = None
    region: Optional[str] = None
    language: Optional[str] = None

    provider: str
    image_url: Optional[str] = None

    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))

    def __repr__(self):
        return f"<SCHOLARSHIP {self.title}>"
