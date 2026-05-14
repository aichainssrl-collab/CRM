from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class LeadModel(BaseModel):
    id: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: str
    phone: Optional[str] = None
    linkedinUrl: Optional[str] = None

    companyName: Optional[str] = None
    companySize: Optional[str] = None
    industry: Optional[str] = None
    roleTitle: Optional[str] = None
    roleSeniority: Optional[str] = None

    source: Optional[str] = None
    utm: Optional[Dict[str, Any]] = None
    landingPage: Optional[str] = None
    referrerUrl: Optional[str] = None

    status: str = "new"
    pipelineStage: str = "new"
    lostReason: Optional[str] = None

    leadScore: int = 0
    isQualified: bool = False
    budgetRange: Optional[str] = None
    timeline: Optional[str] = None
    painPoints: List[str] = []

    notes: Optional[str] = None
    tags: List[str] = []
    customFields: Dict[str, Any] = {}

    assignedTo: Optional[str] = None
    activityCount: int = 0
    taskCount: int = 0
    firstContactAt: Optional[datetime] = None
    lastActivityAt: Optional[datetime] = None

    # Apollo enrichment
    apolloId: Optional[str] = None
    apolloScore: Optional[int] = None
    enrichedAt: Optional[datetime] = None
    enrichmentSource: Optional[str] = None
    numEmployeesRange: Optional[str] = None

    createdAt: datetime
    updatedAt: datetime
    deletedAt: Optional[datetime] = None
