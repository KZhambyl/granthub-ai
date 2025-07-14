from typing import Optional
from datetime import datetime
from .baseSchema import BaseOpportunitySchema

class InternshipBase(BaseOpportunitySchema):
    duration: Optional[str] = None
    paid: Optional[bool] = None

class InternshipCreate(InternshipBase):
    pass

class InternshipRead(InternshipBase):
    id: int
    created_at: datetime
    updated_at: datetime

class InternshipUpdate(InternshipBase):
    title: Optional[str] = None