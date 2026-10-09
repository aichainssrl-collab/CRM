"""
System stats service — admin overview of data counts and health.
"""
from datetime import datetime, timezone, timedelta
from app.services.db_service import db
import logging

logger = logging.getLogger(__name__)


async def get_system_stats() -> dict:
    """Get comprehensive system statistics."""
    now = datetime.now(timezone.utc)
    since30 = now - timedelta(days=30)
    since7 = now - timedelta(days=7)

    # Entity counts
    leads_total = await db["leads"].count_documents({"deletedAt": None})
    leads_7d = await db["leads"].count_documents({"deletedAt": None, "createdAt": {"$gte": since7}})
    leads_30d = await db["leads"].count_documents({"deletedAt": None, "createdAt": {"$gte": since30}})

    deals_total = await db["deals"].count_documents({"deletedAt": None})
    deals_won = await db["deals"].count_documents({"deletedAt": None, "stage": "won"})
    deals_active = await db["deals"].count_documents({"deletedAt": None, "stage": {"$nin": ["won", "lost"]}})

    tasks_total = await db["tasks"].count_documents({"deletedAt": None})
    tasks_open = await db["tasks"].count_documents({"deletedAt": None, "status": "open"})

    users_total = await db["users"].count_documents({"deletedAt": None})
    users_active = await db["users"].count_documents({"deletedAt": None, "isActive": True})

    bookings_total = await db["bookings"].count_documents({"deletedAt": None})

    sequences_total = await db["email_sequences"].count_documents({"deletedAt": None})
    sequences_active = await db["email_sequences"].count_documents({"deletedAt": None, "isActive": True})

    reports_total = await db["reports"].count_documents({"deletedAt": None})

    # Email sends
    emails_sent = await db["email_sends"].count_documents({})
    emails_30d = await db["email_sends"].count_documents({"sentAt": {"$gte": since30}})

    # Form submissions
    forms_total = await db["form_submissions"].count_documents({})

    # GDPR consents
    consents_total = await db["gdpr_consents"].count_documents({})

    # DB size estimate
    collections = await db.list_collection_names()
    doc_count = 0
    for col in collections:
        try:
            doc_count += await db[col].count_documents({})
        except Exception:
            pass

    return {
        "entities": {
            "leads": {"total": leads_total, "last7d": leads_7d, "last30d": leads_30d},
            "deals": {"total": deals_total, "won": deals_won, "active": deals_active},
            "tasks": {"total": tasks_total, "open": tasks_open},
            "users": {"total": users_total, "active": users_active},
            "bookings": {"total": bookings_total},
            "emailSequences": {"total": sequences_total, "active": sequences_active},
            "reports": {"total": reports_total},
            "formSubmissions": {"total": forms_total},
            "gdprConsents": {"total": consents_total},
        },
        "emails": {"sent": emails_sent, "last30d": emails_30d},
        "database": {
            "collections": len(collections),
            "totalDocuments": doc_count,
        },
    }