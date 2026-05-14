from pydantic import BaseModel
from typing import Optional


class UserRecord(BaseModel):
    uid: str
    email: Optional[str] = None
    role: str = "readonly"
    displayName: Optional[str] = None
