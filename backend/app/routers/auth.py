from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import auth
from app.deps import require_admin, UserRecord
from app.services.db_service import db, utcnow
from pydantic import BaseModel, EmailStr

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    temporary_password: str


@router.post("/users", status_code=201)
async def create_crm_user(data: UserCreate, admin: UserRecord = Depends(require_admin)):
    """Crea utente in Firebase Auth + documento MongoDB /users/{uid}."""
    if data.role not in ("admin", "sales", "readonly"):
        raise HTTPException(400, "Ruolo non valido: admin | sales | readonly")

    try:
        firebase_user = auth.create_user(
            email=data.email,
            password=data.temporary_password,
            display_name=data.full_name,
        )
    except auth.EmailAlreadyExistsError:
        raise HTTPException(409, f"Utente con email {data.email} già esistente")
    except Exception as exc:
        raise HTTPException(400, f"Errore creazione auth: {exc}")

    now = utcnow()
    await db["users"].insert_one({
        "_id": firebase_user.uid,
        "uid": firebase_user.uid,
        "email": data.email,
        "displayName": data.full_name,
        "role": data.role,
        "isActive": True,
        "createdAt": now,
        "updatedAt": now,
    })

    return {"uid": firebase_user.uid, "email": data.email, "role": data.role}
