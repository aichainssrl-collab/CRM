from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ActivityBase(BaseModel):
    type: str
    title: Optional[str] = None
    body: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ActivityCreate(ActivityBase):
    userId: Optional[str] = None

class ActivityResponse(ActivityBase):
    id: str
    leadId: str
    userId: Optional[str] = None
    createdAt: datetime
