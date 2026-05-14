from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    priority: str
    dueDate: datetime
    reminderAt: Optional[datetime] = None
    assignedTo: str
    dealId: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    dueDate: Optional[datetime] = None
    completedAt: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: str
    leadId: str
    createdBy: str
    completedAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None
