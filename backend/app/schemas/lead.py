from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UTM(BaseModel):
    source: Optional[str] = None
    medium: Optional[str] = None
    campaign: Optional[str] = None
    content: Optional[str] = None
    term: Optional[str] = None

class LeadBase(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    linkedinUrl: Optional[str] = None
    
    companyName: Optional[str] = None
    companySize: Optional[str] = None
    industry: Optional[str] = None
    roleTitle: Optional[str] = None
    roleSeniority: Optional[str] = None

    source: Optional[str] = None
    utm: Optional[UTM] = None
    landingPage: Optional[str] = None
    referrerUrl: Optional[str] = None

    status: str = "new"
    pipelineStage: str = "new"
    lostReason: Optional[str] = None

    leadScore: int = 0
    isQualified: bool = False
    budgetRange: Optional[str] = None
    timeline: Optional[str] = None
    painPoints: List[str] = Field(default_factory=list)

    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    customFields: Dict[str, Any] = Field(default_factory=dict)

    assignedTo: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phone: Optional[str] = None
    linkedinUrl: Optional[str] = None
    companyName: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    assignedTo: Optional[str] = None
    tags: Optional[List[str]] = None

class LeadStageUpdate(BaseModel):
    status: str
    pipelineStage: str
    lostReason: Optional[str] = None

class LeadResponse(LeadBase):
    id: str
    activityCount: int = 0
    taskCount: int = 0
    firstContactAt: Optional[datetime] = None
    lastActivityAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None
