"""
Create MongoDB indexes for production performance.
Run: python init_db.py
"""
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDEXES = {
    "leads": [
        [("email", 1)],  # unique-ish (app-level enforced)
        [("status", 1)],
        [("createdAt", -1)],
        [("source", 1)],
        [("leadScore", -1)],
        [("deletedAt", 1)],
    ],
    "deals": [
        [("stage", 1)],
        [("leadId", 1)],
        [("assignedTo", 1)],
        [("createdAt", -1)],
        [("expectedClose", 1)],
        [("deletedAt", 1)],
    ],
    "tasks": [
        [("status", 1)],
        [("dueDate", 1)],
        [("assignedTo", 1)],
        [("deletedAt", 1)],
    ],
    "users": [
        [("email", 1)],
        [("role", 1)],
        [("isActive", 1)],
    ],
    "activities": [
        [("leadId", 1)],
        [("createdAt", -1)],
    ],
    "form_submissions": [
        [("formType", 1)],
        [("createdAt", -1)],
    ],
    "bookings": [
        [("preferredDate", 1)],
        [("status", 1)],
        [("createdAt", -1)],
    ],
    "gdpr_consents": [
        [("leadId", 1)],
        [("consentType", 1)],
        [("timestamp", -1)],
    ],
    "email_sequences": [
        [("isActive", 1)],
        [("createdAt", -1)],
        [("deletedAt", 1)],
    ],
    "email_sends": [
        [("sequenceId", 1)],
        [("leadId", 1)],
        [("sentAt", -1)],
    ],
    "reports": [
        [("createdAt", -1)],
        [("deletedAt", 1)],
    ],
    "marketing_conversations": [
        [("createdBy", 1)],
        [("updatedAt", -1)],
    ],
}


async def create_indexes():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    for collection_name, indexes in INDEXES.items():
        collection = db[collection_name]
        for idx in indexes:
            try:
                await collection.create_index(idx)
                logger.info(f"Created index on {collection_name}: {idx}")
            except Exception as e:
                logger.warning(f"Index on {collection_name} {idx}: {e}")

    # Unique index on users._id is implicit; add email unique if desired
    try:
        await db["users"].create_index([("email", 1)], unique=True, sparse=True)
        logger.info("Created unique index on users.email")
    except Exception as e:
        logger.warning(f"users.email unique index: {e}")

    logger.info("Index creation complete.")
    client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())