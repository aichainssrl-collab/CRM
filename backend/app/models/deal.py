from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DealModel(BaseModel):
    id: str
    leadId: str
    title: str
    value: Optional[float] = None
    currency: str = "EUR"
    stage: str = "qualification"  # qualification, proposal, negotiation, closed_won, closed_lost
    probability: int = 0
    expectedCloseDate: Optional[datetime] = None
    lostReason: Optional[str] = None
    assignedTo: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []
    createdBy: str
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None
