from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    uid: str
    email: EmailStr
    displayName: Optional[str] = None
    role: str = "sales"  # admin, sales, readonly


class UserUpdate(BaseModel):
    displayName: Optional[str] = None
    role: Optional[str] = None
    isActive: Optional[bool] = None


class UserResponse(BaseModel):
    uid: str
    email: str
    displayName: Optional[str] = None
    role: str
    isActive: bool
    createdAt: datetime
    updatedAt: datetime


class UserMeResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    displayName: Optional[str] = None
    role: str
