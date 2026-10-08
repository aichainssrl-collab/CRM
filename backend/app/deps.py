import asyncio
import logging
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from app.services.db_service import get_document
from app.models.user import UserRecord

logger = logging.getLogger(__name__)
security = HTTPBearer()


def _verify_token_sync(token: str) -> dict:
    """Wrapper sincrono per verify_id_token — eseguito nel thread pool."""
    return auth.verify_id_token(token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserRecord:
    """
    Verifica Firebase ID token (in thread pool per non bloccare l'event loop)
    e carica il profilo utente da MongoDB.
    """
    # 1. Verifica token Firebase — eseguita in thread pool (chiamata SINCRONA bloccante)
    try:
        loop = asyncio.get_event_loop()
        decoded = await loop.run_in_executor(None, _verify_token_sync, credentials.credentials)
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")
    except Exception as e:
        logger.warning("verify_id_token failed: %s: %s", type(e).__name__, e)
        raise HTTPException(status_code=401, detail="Autenticazione fallita")

    uid = decoded["uid"]

    # 2. Carica utente da MongoDB (asincrono, non blocca l'event loop)
    try:
        user_data = await get_document("users", uid)
    except Exception as e:
        logger.error("MongoDB get_document('users', %s) failed: %s", uid, e, exc_info=True)
        raise HTTPException(status_code=503, detail="Database non disponibile")

    if not user_data:
        logger.warning("User %s authenticated via Firebase but not in MongoDB", uid)
        raise HTTPException(status_code=403, detail="Utente non registrato nel CRM")

    if not user_data.get("isActive", False):
        raise HTTPException(status_code=403, detail="Account disattivato")

    return UserRecord(
        uid=uid,
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
