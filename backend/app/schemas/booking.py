from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class BookingSlotResponse(BaseModel):
    id: str
    startTime: datetime
    endTime: datetime
    isAvailable: bool


class BookingCreate(BaseModel):
    slotId: str
    firstName: str
    lastName: str
    email: EmailStr
    phone: Optional[str] = None
    companyName: Optional[str] = None
    message: Optional[str] = None
    consent_given: bool
    consent_text: str = "Acconsento al trattamento dei dati personali ai sensi dell'art. 13 GDPR."


class BookingResponse(BaseModel):
    id: str
    slotId: str
    leadId: Optional[str] = None
    firstName: str
    lastName: str
    email: str
    status: str
    createdAt: datetime


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = None
