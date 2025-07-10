from pydantic import BaseModel
from datetime import date
from typing import Optional

class GrantBase(BaseModel):
    title: str
    deadline: Optional[date] = None
    amount: Optional[str] = None

class GrantCreate(GrantBase):
    pass

class GrantOut(GrantBase):
    id: int

    class Config:
        orm_mode = True
