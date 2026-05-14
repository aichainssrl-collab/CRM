from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

class FormBase(BaseModel):
    email: EmailStr
    consent_given: bool
    consent_text: str

class PlaybookFormData(FormBase):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    companyName: Optional[str] = None
    
class ContactFormData(FormBase):
    firstName: str
    lastName: str
    message: str
    companyName: Optional[str] = None
    phone: Optional[str] = None
