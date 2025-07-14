from sqlmodel import SQLModel, Field
from typing import Optional
from .baseModel import BaseOpportunity

class Internship(BaseOpportunity, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    duration: Optional[str] = None
    paid: Optional[bool] = None