from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskModel(BaseModel):
    id: str
    leadId: str
    title: str
    description: Optional[str] = None
    dueDate: Optional[datetime] = None
    assignedTo: Optional[str] = None
    status: str = "open"  # open, completed, cancelled
    completedAt: Optional[datetime] = None
    createdBy: str
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None
