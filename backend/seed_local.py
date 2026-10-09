"""
Seed local MongoDB with development data.
Run: python seed_local.py
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid.uuid4())


USERS = [
    {"_id": "eHFeSPGP8cWxWHFcM5In4KVYQQ42", "email": "fred@it.it", "displayName": "Fred Admin", "role": "admin", "isActive": True},
    {"_id": "fFW6zJBJxCYQ77y0vXskwuFQEIH3", "email": "admin@aichain.it", "displayName": "Admin AiChain", "role": "admin", "isActive": True},
    {"_id": "JY9qlgBlfWMmtSLo4n2bjte6q8Z2", "email": "marketing@aichainsolutions.net", "displayName": "Marketing User", "role": "sales", "isActive": True},
    {"_id": "VWhvlNibVsbjNMX8wu238Wvt3IE3", "email": "fredyh@aichain.it", "displayName": "Fred Super Admin", "role": "admin", "isActive": True},
]


def make_lead(first, last, company, email, source, status, score, industry=None):
    now = utcnow()
    return {
        "_id": uid(),
        "firstName": first,
        "lastName": last,
        "companyName": company,
        "email": email,
        "phone": "+39 095 0000000",
        "source": source,
        "status": status,
        "leadScore": score,
        "industry": industry,
        "tags": [],
        "assignedTo": None,
        "deletedAt": None,
        "createdAt": now - timedelta(days=score),
        "updatedAt": now,
    }


SAMPLE_LEADS = [
    make_lead("Mario", "Rossi", "Studio Rossi & Associati", "mario@rossi.it", "playbook", "qualified", 85, "Legal"),
    make_lead("Giulia", "Bianchi", "Bianchi Legal", "giulia@bianchilegal.it", "contact", "contacted", 60, "Legal"),
    make_lead("Luca", "Verdi", "Verdi Commercialisti", "luca@verdicom.it", "excel_import", "new", 40, "Accounting"),
    make_lead("Anna", "Neri", "Neri & Partners", "anna@neripartners.it", "booking", "proposal", 92, "Legal"),
    make_lead("Paolo", "Gallo", "Gallo Ingegneria", "paolo@galloing.it", "assessment", "negotiation", 78, "Engineering"),
    make_lead("Sara", "Costa", "Costa Notai", "sara@costanotai.it", "playbook", "new", 55, "Legal"),
    make_lead("Marco", "Ferrari", "Ferrari Consulting", "marco@ferraricons.it", "referral", "won", 95, "Consulting"),
    make_lead("Elena", "Conti", "Conti Studio", "elena@contistudio.it", "linkedin", "contacted", 48, "Legal"),
]


def make_deal(lead_id, title, value, stage, prob, assigned="eHFeSPGP8cWxWHFcM5In4KVYQQ42"):
    now = utcnow()
    return {
        "_id": uid(),
        "leadId": lead_id,
        "title": title,
        "value": value,
        "probability": prob,
        "expectedClose": now + timedelta(days=30),
        "stage": stage,
        "product": "ZenTratto",
        "notes": "",
        "assignedTo": assigned,
        "closedAt": None,
        "deletedAt": None,
        "createdAt": now - timedelta(days=15),
        "updatedAt": now,
    }


SAMPLE_SEQUENCE = {
    "_id": uid(),
    "name": "Welcome Playbook",
    "description": "Sequenza di benvenuto dopo il download del Playbook",
    "isActive": False,
    "enrollments": [],
    "createdBy": "eHFeSPGP8cWxWHFcM5In4KVYQQ42",
    "steps": [
        {"subject": "Ecco il tuo AiChain Playbook", "bodyHtml": "<p>Ciao {firstName}!</p><p>Ecco il playbook che hai richiesto.</p>", "delayDays": 0},
        {"subject": "Come può aiutarti AiChain", "bodyHtml": "<p>Ciao {firstName},</p><p>Scopri come ZenTratto può trasformare il tuo studio.</p>", "delayDays": 3},
        {"subject": "Prenota una demo gratuita", "bodyHtml": "<p>Ciao {firstName}!</p><p>Pronto a vedere ZenTratto in azione? Prenota una demo.</p>", "delayDays": 5},
    ],
}


async def seed():
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    # Users (upsert by _id)
    for u in USERS:
        u["createdAt"] = utcnow()
        u["updatedAt"] = utcnow()
        u["deletedAt"] = None
        await db["users"].update_one({"_id": u["_id"]}, {"$set": u}, upsert=True)
    logger.info(f"Seeded {len(USERS)} users")

    # Leads (insert if empty)
    lead_count = await db["leads"].count_documents({})
    if lead_count == 0:
        await db["leads"].insert_many(SAMPLE_LEADS)
        logger.info(f"Seeded {len(SAMPLE_LEADS)} leads")
    else:
        logger.info(f"Leads already present ({lead_count}), skipping")

    # Deals (insert if empty)
    deal_count = await db["deals"].count_documents({})
    if deal_count == 0:
        leads = await db["leads"].find({"deletedAt": None}).to_list(10)
        if leads:
            sample_deals = [
                make_deal(leads[0]["_id"], "ZenTratto — Studio Rossi", 15000, "proposal", 60),
                make_deal(leads[3]["_id"], "SignSiSure — Neri & Partners", 25000, "negotiation", 75),
                make_deal(leads[4]["_id"], "Enterprise Agent — Gallo", 40000, "qualified", 50),
                make_deal(leads[6]["_id"], "ZenTratto — Ferrari Consulting", 18000, "won", 100),
            ]
            await db["deals"].insert_many(sample_deals)
            logger.info(f"Seeded {len(sample_deals)} deals")

    # Email sequence
    seq_count = await db["email_sequences"].count_documents({})
    if seq_count == 0:
        now = utcnow()
        SAMPLE_SEQUENCE["createdAt"] = now
        SAMPLE_SEQUENCE["updatedAt"] = now
        SAMPLE_SEQUENCE["deletedAt"] = None
        await db["email_sequences"].insert_one(SAMPLE_SEQUENCE)
        logger.info("Seeded 1 email sequence")

    logger.info("Seed complete.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())