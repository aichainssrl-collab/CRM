from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DealBase(BaseModel):
    title: str
    value: Optional[float] = None
    probability: int = 0
    expectedClose: Optional[datetime] = None
    stage: str
    product: Optional[str] = None
    notes: Optional[str] = None
    assignedTo: Optional[str] = None

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    probability: Optional[int] = None
    expectedClose: Optional[datetime] = None
    stage: Optional[str] = None
    notes: Optional[str] = None

class DealResponse(DealBase):
    id: str
    leadId: str
    createdAt: datetime
    updatedAt: datetime
    closedAt: Optional[datetime] = None
    deletedAt: Optional[datetime] = None
