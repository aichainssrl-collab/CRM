from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class ActivityModel(BaseModel):
    id: str
    leadId: str
    type: str  # note, call, email, meeting, stage_changed, form_submitted, task_completed
    title: Optional[str] = None
    body: Optional[str] = None
    userId: Optional[str] = None
    metadata: Dict[str, Any] = {}
    createdAt: datetime
