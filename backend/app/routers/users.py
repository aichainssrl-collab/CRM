from fastapi import APIRouter, Depends, HTTPException
from app.deps import require_admin, get_current_user, UserRecord
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserMeResponse
from app.services.db_service import create_document, update_document, list_collection, utcnow
from app.firebase_admin import db

router = APIRouter()


@router.get("/me")
async def get_me(user: UserRecord = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse(
        uid=user.uid,
        email=user.email,
        displayName=user.displayName,
        role=user.role,
    )


@router.get("")
async def list_users(user: UserRecord = Depends(require_admin)):
    """Lista tutti gli utenti CRM — solo admin."""
    results = await list_collection("users", include_deleted=False)
    return results


@router.post("", status_code=201)
async def create_user(data: UserCreate, user: UserRecord = Depends(require_admin)):
    """Registra un nuovo membro del team nel CRM."""
    snap = await db.collection("users").document(data.uid).get()
    if snap.exists:
        raise HTTPException(409, f"Utente {data.uid} già registrato")

    payload = {
        **data.model_dump(),
        "isActive": True,
    }
    await db.collection("users").document(data.uid).set({
        **payload,
        "createdAt": utcnow(),
        "updatedAt": utcnow(),
    })
    return {"uid": data.uid, **payload}


@router.patch("/{uid}")
async def update_user(
    uid: str,
    data: UserUpdate,
    user: UserRecord = Depends(require_admin),
):
    snap = await db.collection("users").document(uid).get()
    if not snap.exists:
        raise HTTPException(404, "Utente non trovato")

    updates = data.model_dump(exclude_unset=True)
    updates["updatedAt"] = utcnow()
    await db.collection("users").document(uid).update(updates)

    snap = await db.collection("users").document(uid).get()
    return {"uid": uid, **snap.to_dict()}
