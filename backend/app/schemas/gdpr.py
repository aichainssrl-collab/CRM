from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GdprExportResponse(BaseModel):
    exported_at: str
    lead: Optional[dict] = None
    activities: list[dict] = []
    tasks: list[dict] = []
    gdpr_consents: list[dict] = []


class GdprEraseRequest(BaseModel):
    confirm: bool
    reason: Optional[str] = None


class GdprConsentCreate(BaseModel):
    lead_id: str
    action: str  # granted, revoked
    purpose: str  # marketing, service_communication, profiling
    consent_text: str
    ip: Optional[str] = None
    policy_version: str = "2.1"


class GdprConsentResponse(BaseModel):
    id: str
    leadId: str
    action: str
    purpose: str
    policyVersion: str
    ipAddress: Optional[str]
    dataHash: str
    createdAt: datetime
