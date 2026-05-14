import firebase_admin
from firebase_admin import credentials, firestore_async, storage
from google.cloud import firestore_v1
from app.config import settings
import json
import os

_cred_obj = None  # google.auth credentials, kept for direct Firestore client

def initialize_firebase():
    global _cred_obj

    if firebase_admin._apps:
        return

    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        firebase_admin.initialize_app(options={
            "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
            "projectId": settings.FIREBASE_PROJECT_ID,
        })
        return

    elif settings.GOOGLE_APPLICATION_CREDENTIALS_JSON:
        cred_dict = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
        import google.oauth2.service_account as sa
        _cred_obj = sa.Credentials.from_service_account_info(
            cred_dict,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    else:
        cred = credentials.ApplicationDefault()
        import google.auth
        _cred_obj, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

    firebase_admin.initialize_app(cred, {
        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
        "projectId": settings.FIREBASE_PROJECT_ID,
    })


def _build_firestore_client() -> firestore_v1.AsyncClient:
    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        return firestore_async.client()

    db_id = settings.FIRESTORE_DATABASE_ID
    if db_id == "(default)":
        return firestore_async.client()

    return firestore_v1.AsyncClient(
        project=settings.FIREBASE_PROJECT_ID,
        credentials=_cred_obj,
        database=db_id,
    )


# Inizializza l'app alla prima importazione
initialize_firebase()

# Client globali
db = _build_firestore_client()
bucket = storage.bucket()
