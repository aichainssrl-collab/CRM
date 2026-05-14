from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BookingSlotModel(BaseModel):
    id: str
    startTime: datetime
    endTime: datetime
    isAvailable: bool = True
    bookedBy: Optional[str] = None  # lead email
    bookingId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime


class BookingModel(BaseModel):
    id: str
    slotId: str
    leadId: Optional[str] = None
    firstName: str
    lastName: str
    email: str
    phone: Optional[str] = None
    companyName: Optional[str] = None
    message: Optional[str] = None
    status: str = "confirmed"  # confirmed, cancelled, completed, no_show
    cancelledAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime
