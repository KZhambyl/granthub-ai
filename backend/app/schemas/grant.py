from typing import Optional
from datetime import datetime
from .baseSchema import BaseOpportunitySchema

class GrantBase(BaseOpportunitySchema):
    pass

class GrantCreate(GrantBase):
    pass

class GrantRead(GrantBase):
    id: int
    created_at: datetime
    updated_at: datetime

class GrantUpdate(GrantBase):
    title: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    