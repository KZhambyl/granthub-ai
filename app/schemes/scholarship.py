from typing import Optional
from datetime import datetime
from .baseSchema import BaseOpportunitySchema

class ScholarshipBase(BaseOpportunitySchema):
    level: Optional[str] = None  # bachelor, master, phd

class ScholarshipCreate(ScholarshipBase):
    pass

class ScholarshipRead(ScholarshipBase):
    id: int
    created_at: datetime
    updated_at: datetime

class ScholarshipUpdate(ScholarshipBase):
    title: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    provider: Optional[str] = None
