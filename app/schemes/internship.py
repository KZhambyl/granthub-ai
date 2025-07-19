from typing import Optional
from datetime import datetime
from .baseSchema import BaseOpportunitySchema, BaseOpportunityUpdateSchema

class InternshipBase(BaseOpportunitySchema):
    duration: Optional[str] = None
    paid: Optional[bool] = None

class InternshipCreate(InternshipBase):
    pass

class InternshipRead(InternshipBase):
    id: int
    created_at: datetime
    updated_at: datetime

class InternshipUpdate(BaseOpportunityUpdateSchema):
    duration: Optional[str] = None
    paid: Optional[bool] = None