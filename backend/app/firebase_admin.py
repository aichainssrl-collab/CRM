"""
Firebase Admin — solo autenticazione JWT.
MongoDB gestisce tutti i dati (vedi db_service.py).
"""
import firebase_admin
from firebase_admin import credentials, auth  # noqa: F401 — auth usato via import
from app.config import settings
import json
import os


def initialize_firebase():
    if firebase_admin._apps:
        return

    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        firebase_admin.initialize_app(options={
            "projectId": settings.FIREBASE_PROJECT_ID,
        })
        return

    if settings.GOOGLE_APPLICATION_CREDENTIALS_JSON:
        cred_dict = json.loads(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred, {
        "projectId": settings.FIREBASE_PROJECT_ID,
        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
    })


initialize_firebase()
