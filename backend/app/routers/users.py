from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from firebase_admin import auth, storage as fb_storage
from app.deps import require_admin, get_current_user, UserRecord
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserMeResponse
from app.services.db_service import db, create_document, update_document, list_collection, utcnow

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_AVATAR_SIZE = 1 * 1024 * 1024  # 1 MB


@router.get("/me/avatar")
async def get_avatar(user: UserRecord = Depends(get_current_user)):
    """Restituisce l'URL dell'avatar corrente dell'utente (da MongoDB)."""
    user_doc = await db["users"].find_one({"_id": user.uid}, {"photoURL": 1})
    return {"photoURL": (user_doc or {}).get("photoURL")}


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: UserRecord = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, "Formato non supportato. Usa JPG, PNG, GIF o WebP.")

    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(400, "File troppo grande. Massimo 1 MB.")

    # Upload su Firebase Storage via Admin SDK (nessun CORS necessario)
    bucket = fb_storage.bucket()
    blob = bucket.blob(f"avatars/{user.uid}")
    blob.upload_from_string(content, content_type=file.content_type)
    blob.make_public()
    photo_url = blob.public_url

    # Aggiorna Firebase Auth e MongoDB
    auth.update_user(user.uid, photo_url=photo_url)
    await db["users"].update_one(
        {"_id": user.uid},
        {"$set": {"photoURL": photo_url, "updatedAt": utcnow()}},
    )

    return {"photoURL": photo_url}


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
    return await list_collection("users", include_deleted=False)


@router.post("", status_code=201)
async def create_user(data: UserCreate, user: UserRecord = Depends(require_admin)):
    existing = await db["users"].find_one({"_id": data.uid})
    if existing:
        raise HTTPException(409, f"Utente {data.uid} già registrato")

    payload = {**data.model_dump(), "isActive": True}
    await db["users"].insert_one({
        "_id": data.uid,
        **payload,
        "createdAt": utcnow(),
        "updatedAt": utcnow(),
    })
    return {"uid": data.uid, **payload}


@router.patch("/{uid}")
async def update_user(uid: str, data: UserUpdate, user: UserRecord = Depends(require_admin)):
    existing = await db["users"].find_one({"_id": uid})
    if not existing:
        raise HTTPException(404, "Utente non trovato")

    updates = {**data.model_dump(exclude_unset=True), "updatedAt": utcnow()}
    doc = await db["users"].find_one_and_update(
        {"_id": uid}, {"$set": updates}, return_document=True
    )
    doc = dict(doc)
    doc["uid"] = doc.pop("_id")
    return doc
