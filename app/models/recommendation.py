from sqlmodel import SQLModel, Field, Column
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
import sqlalchemy.dialects.postgresql as pg


class ItemType(str, Enum):
    grant = "grant"
    internship = "internship"
    scholarship = "scholarship"


class Recommendation(SQLModel, table=True):
    __tablename__ = "recommendations"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

    user_id: UUID = Field(foreign_key="users.uid", index=True)
    item_id: int = Field(index=True)

    item_type: ItemType = Field(index=True)

    score: float = Field(default=0.0)
    source_model: str = Field(default="baseline")

    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
