from typing import Optional
from datetime import datetime
from .baseSchema import BaseOpportunitySchema, BaseOpportunityUpdateSchema

class GrantBase(BaseOpportunitySchema):
    pass

class GrantCreate(GrantBase):
    pass

class GrantRead(GrantBase):
    id: int
    created_at: datetime
    updated_at: datetime

class GrantUpdate(BaseOpportunityUpdateSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    