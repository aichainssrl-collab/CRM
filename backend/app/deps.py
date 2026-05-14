from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from app.firebase_admin import db
from app.models.user import UserRecord

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserRecord:
    """Verifica Firebase ID token e carica il profilo utente da Firestore."""
    try:
        decoded = auth.verify_id_token(credentials.credentials)
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")
    except Exception:
        raise HTTPException(status_code=401, detail="Autenticazione fallita")

    snap = await db.collection("users").document(decoded["uid"]).get()
    if not snap.exists:
        raise HTTPException(status_code=403, detail="Utente non registrato nel CRM")

    user_data = snap.to_dict()
    if not user_data.get("isActive", False):
        raise HTTPException(status_code=403, detail="Account disattivato")

    return UserRecord(
        uid=decoded["uid"],
        email=decoded.get("email"),
        role=user_data.get("role", "readonly"),
        displayName=user_data.get("displayName"),
    )


async def require_admin(user: UserRecord = Depends(get_current_user)) -> UserRecord:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Richiesti permessi admin")
    return user


async def require_sales(user: UserRecord = Depends(get_current_user)) -> UserRecord:
    if user.role not in ("admin", "sales"):
        raise HTTPException(status_code=403, detail="Richiesti permessi sales")
    return user
