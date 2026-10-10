"""
Seed DEMO data — one (or few) examples per CRM module.

Idempotent: uses fixed `demo-*` ids and upserts.
Run:  python seed_demo.py
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

from app.config import settings
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_demo")

ADMIN = "eHFeSPGP8cWxWHFcM5In4KVYQQ42"
SALES = "JY9qlgBlfWMmtSLo4n2bjte6q8Z2"
NOW = datetime.now(timezone.utc)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def days(n: int) -> datetime:
    return utcnow() + timedelta(days=n)


# ── Fixed demo ids ───────────────────────────────────────────────────────────
LEAD = "demo-lead-1"
LEAD2 = "demo-lead-2"
DEAL = "demo-deal-1"
TASK = "demo-task-1"
PRODUCT = "demo-product-1"
PROPOSAL = "demo-proposal-1"
INVOICE = "demo-invoice-1"
WORKFLOW = "demo-workflow-1"
CONTENT = "demo-content-1"
TEMPLATE = "demo-template-1"
SEQUENCE = "demo-sequence-1"
COMPETITOR = "demo-competitor-1"
SNAPSHOT = "demo-snapshot-1"
CONVERSATION = "demo-wa-1"
MESSAGE = "demo-wa-msg-1"
NOTIFICATION = "demo-notif-1"
BOOKING = "demo-booking-1"
REPORT = "demo-report-1"
SEGMENT = "demo-segment-1"
ACTIVITY = "demo-activity-1"
FORM = "demo-form-1"
ENROLLMENT = "demo-enroll-1"


def base(id_: str) -> dict:
    return {
        "_id": id_,
        "createdAt": utcnow(),
        "updatedAt": utcnow(),
        "deletedAt": None,
    }


async def upsert(db, col: str, doc: dict) -> None:
    payload = {**base(doc["_id"]), **doc}
    await db[col].update_one({"_id": doc["_id"]}, {"$set": payload}, upsert=True)
    logger.info("upsert %s/%s", col, doc["_id"])


async def seed() -> None:
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]

    # ── 1. Lead (referenced by most demos) ──────────────────────────────────
    await upsert(db, "leads", {
        "_id": LEAD,
        "firstName": "Demo",
        "lastName": "Cliente",
        "companyName": "Demo Studio Legale SRL",
        "email": "demo.cliente@example.com",
        "phone": "+39 095 1112223",
        "linkedinUrl": "https://linkedin.com/in/democliente",
        "industry": "Legal",
        "companySize": "11-50",
        "roleTitle": "Managing Partner",
        "roleSeniority": "c_suite",
        "source": "demo",
        "status": "qualified",
        "pipelineStage": "qualified",
        "leadScore": 88,
        "tags": ["demo", "legal"],
        "notes": "Lead demo per esplorare il CRM",
        "assignedTo": ADMIN,
        "activityCount": 1,
        "taskCount": 1,
        "apolloId": "apollo-demo-1",
        "apolloScore": 88,
        "enrichedAt": utcnow(),
        "enrichmentSource": "apollo",
        "numEmployeesRange": "11-50",
        "customFields": {},
        "painPoints": ["gestione documentale", "compliance GDPR"],
    })
    await upsert(db, "leads", {
        "_id": LEAD2,
        "firstName": "Demo",
        "lastName": "Prospect",
        "companyName": "Prospect SpA",
        "email": "demo.prospect@example.com",
        "source": "apollo_import",
        "status": "new",
        "pipelineStage": "new",
        "leadScore": 52,
        "tags": ["demo", "apollo"],
        "assignedTo": SALES,
        "activityCount": 0,
        "taskCount": 0,
        "customFields": {},
        "painPoints": [],
    })

    # ── 2. Activity ─────────────────────────────────────────────────────────
    await upsert(db, "activities", {
        "_id": ACTIVITY,
        "leadId": LEAD,
        "type": "call",
        "title": "Call introduttiva",
        "description": "Presentazione ZenTratto, interesse su RAG documentale",
        "userId": ADMIN,
        "metadata": {"durationMin": 25},
    })

    # ── 3. Task ─────────────────────────────────────────────────────────────
    await upsert(db, "tasks", {
        "_id": TASK,
        "title": "Inviare proposta ZenTratto",
        "description": "Preparare preventivo con linee prodotto e inviare via email",
        "leadId": LEAD,
        "dealId": DEAL,
        "assignedTo": ADMIN,
        "status": "open",
        "priority": "high",
        "dueDate": days(3),
    })

    # ── 4. Deal ─────────────────────────────────────────────────────────────
    await upsert(db, "deals", {
        "_id": DEAL,
        "leadId": LEAD,
        "title": "ZenTratto — Demo Studio Legale",
        "value": 18000,
        "probability": 65,
        "expectedClose": days(21),
        "stage": "proposal",
        "product": "ZenTratto",
        "notes": "Demo completata, in attesa di approvazione budget",
        "assignedTo": ADMIN,
        "closedAt": None,
    })

    # ── 5. Products ─────────────────────────────────────────────────────────
    await upsert(db, "products", {
        "_id": PRODUCT,
        "name": "ZenTratto",
        "sku": "ZT-001",
        "description": "RAG documentale enterprise — ricerca semantica su archivi",
        "category": "Platform",
        "unitPrice": 15000,
        "currency": "EUR",
        "taxRate": 22,
        "isActive": True,
        "tags": ["rag", "document-ai"],
        "createdBy": ADMIN,
    })
    await upsert(db, "products", {
        "_id": "demo-product-2",
        "name": "SignSiSure",
        "sku": "SS-001",
        "description": "Firma eIDAS 2.0 + audit trail blockchain",
        "category": "Compliance",
        "unitPrice": 8000,
        "currency": "EUR",
        "taxRate": 22,
        "isActive": True,
        "tags": ["eidas", "signature"],
        "createdBy": ADMIN,
    })
    await upsert(db, "products", {
        "_id": "demo-product-3",
        "name": "Enterprise Agent",
        "sku": "EA-001",
        "description": "Agent AI per classificazione e workflow documentali",
        "category": "AI",
        "unitPrice": 12000,
        "currency": "EUR",
        "taxRate": 22,
        "isActive": True,
        "tags": ["ai", "workflow"],
        "createdBy": ADMIN,
    })

    # ── 6. Segment (userId + isGlobal — see segmentation_service.list_segments) ──
    await upsert(db, "segments", {
        "_id": SEGMENT,
        "userId": ADMIN,
        "name": "Studi legali qualificati",
        "description": "Lead Legal con score > 70 e status qualified",
        "rules": {
            "industry": "Legal",
            "status": "qualified",
        },
        "entityType": "leads",
        "isGlobal": True,
    })

    # ── 7. Proposal ─────────────────────────────────────────────────────────
    now = utcnow()
    items = [{
        "productId": PRODUCT,
        "name": "ZenTratto",
        "description": "Licenza annuale + onboarding",
        "quantity": 1,
        "unitPrice": 15000,
        "total": 15000,
    }]
    subtotal = 15000
    tax = subtotal * 0.22
    await upsert(db, "proposals", {
        "_id": PROPOSAL,
        "number": "PROP-2026-0001",
        "title": "Proposta ZenTratto — Demo Studio Legale",
        "clientName": "Demo Studio Legale SRL",
        "clientEmail": "demo.cliente@example.com",
        "leadId": LEAD,
        "dealId": DEAL,
        "status": "draft",
        "items": items,
        "subtotal": subtotal,
        "taxRate": 22,
        "taxAmount": tax,
        "total": subtotal + tax,
        "currency": "EUR",
        "validUntil": days(30),
        "notes": "Proposta demo — valida 30 giorni",
        "sentAt": None,
        "acceptedAt": None,
        "rejectedAt": None,
    })

    # ── 8. Invoice ──────────────────────────────────────────────────────────
    await upsert(db, "invoices", {
        "_id": INVOICE,
        "number": "INV-2026-0001",
        "title": "Fattura ZenTratto — acconto 50%",
        "clientName": "Demo Studio Legale SRL",
        "clientEmail": "demo.cliente@example.com",
        "leadId": LEAD,
        "proposalId": PROPOSAL,
        "status": "issued",
        "items": items,
        "subtotal": subtotal,
        "taxRate": 22,
        "taxAmount": tax,
        "total": subtotal + tax,
        "currency": "EUR",
        "dueDate": days(15),
        "paidAt": None,
        "notes": "Fattura demo",
    })

    # ── 9. Workflow ─────────────────────────────────────────────────────────
    await upsert(db, "workflows", {
        "_id": WORKFLOW,
        "name": "Auto-assign Legal leads",
        "description": "Quando un lead Legal arriva, assegna ad admin e crea task follow-up",
        "trigger": "lead_created",
        "conditions": [
            {"field": "industry", "op": "eq", "value": "Legal"},
        ],
        "actions": [
            {"type": "assign", "userId": ADMIN},
            {"type": "create_task", "title": "Follow-up lead Legal", "dueInDays": 2},
        ],
        "isActive": True,
        "createdBy": ADMIN,
    })

    # ── 10. Content (collection is content_library) ─────────────────────────
    await upsert(db, "content_library", {
        "_id": CONTENT,
        "title": "Playbook AI per studi legali",
        "type": "blog",
        "body": "Guida pratica per introdurre l'AI nello studio legale…",
        "description": "Come ZenTratto riduce il tempo di ricerca documentale",
        "tags": ["playbook", "legal", "ai"],
        "language": "it",
        "source": "manual",
        "createdBy": ADMIN,
    })

    # ── 11. Email template ──────────────────────────────────────────────────
    await upsert(db, "email_templates", {
        "_id": TEMPLATE,
        "name": "Welcome demo",
        "subject": "Benvenuto {{firstName}} — ecco il playbook",
        "bodyHtml": "<p>Ciao {{firstName}},</p><p>Grazie per l'interesse!</p>",
        "category": "welcome",
        "isDefault": False,
        "createdBy": ADMIN,
    })

    # ── 12. Email sequence + enrollment ─────────────────────────────────────
    await upsert(db, "email_sequences", {
        "_id": SEQUENCE,
        "name": "Nurture Demo",
        "description": "3 step dopo il primo contatto",
        "isActive": True,
        "steps": [
            {"subject": "Ciao {{firstName}}", "bodyHtml": "<p>Step 1</p>", "delayDays": 0},
            {"subject": "Case study ZenTratto", "bodyHtml": "<p>Step 2</p>", "delayDays": 3},
            {"subject": "Prenota una call", "bodyHtml": "<p>Step 3</p>", "delayDays": 7},
        ],
        "enrollments": [{
            "id": ENROLLMENT,
            "leadId": LEAD,
            "leadEmail": "demo.cliente@example.com",
            "leadName": "Demo Cliente",
            "currentStep": 1,
            "status": "active",
            "startedAt": utcnow(),
            "nextSendAt": days(2),
            "completedAt": None,
        }],
        "createdBy": ADMIN,
    })

    # ── 13. Competitor + snapshot + change ───────────────────────────────────
    await upsert(db, "competitors", {
        "_id": COMPETITOR,
        "name": "DocuAI Competitor",
        "website": "https://competitor.example",
        "description": "Player RAG documentale",
        "tags": ["rag"],
        "status": "active",
        "lastCheckedAt": utcnow(),
        "lastChangeAt": days(-1),
        "changeCount": 1,
        "createdBy": ADMIN,
    })
    await upsert(db, "competitor_snapshots", {
        "_id": SNAPSHOT,
        "competitorId": COMPETITOR,
        "url": "https://competitor.example",
        "title": "DocuAI — Document AI",
        "metaDescription": "AI per documenti",
        "headings": ["Prezzi", "Features"],
        "pricingMentions": ["Piani da 99 EUR"],
        "pricingKeywords": ["prezzo"],
        "bodyExcerpt": "…",
        "bodyHash": "abc123",
        "capturedAt": utcnow(),
    })
    await upsert(db, "competitor_changes", {
        "_id": "demo-change-1",
        "competitorId": COMPETITOR,
        "field": "pricingMentions",
        "from": "Piani da 79 EUR",
        "to": "Piani da 99 EUR",
        "detectedAt": days(-1),
    })

    # ── 14. WhatsApp conversation + message ──────────────────────────────────
    await upsert(db, "whatsapp_conversations", {
        "_id": CONVERSATION,
        "phone": "+393331234567",
        "leadId": LEAD,
        "leadName": "Demo Cliente",
        "status": "open",
        "lastMessageAt": utcnow(),
        "lastInboundAt": utcnow(),
        "lastOutboundAt": None,
        "unreadCount": 1,
        "assignedTo": ADMIN,
        "createdBy": ADMIN,
    })
    await upsert(db, "whatsapp_messages", {
        "_id": MESSAGE,
        "conversationId": CONVERSATION,
        "direction": "inbound",
        "body": "Salve, vorrei info su ZenTratto",
        "status": "received",
        "waMessageId": "demo-wa-id-1",
    })

    # ── 15. Notification ────────────────────────────────────────────────────
    await upsert(db, "notifications", {
        "_id": NOTIFICATION,
        "userId": ADMIN,
        "title": "Nuovo lead demo",
        "body": "Demo Cliente è stato assegnato a te",
        "kind": "info",
        "link": f"/crm/leads/{LEAD}",
        "readAt": None,
    })

    # ── 16. Booking (calendar reads preferredDate + firstName/lastName) ─────
    await upsert(db, "bookings", {
        "_id": BOOKING,
        "leadId": LEAD,
        "slotId": "demo-slot-1",
        "status": "confirmed",
        "preferredDate": days(2),
        "firstName": "Demo",
        "lastName": "Cliente",
        "email": "demo.cliente@example.com",
        "timeSlot": "10:00",
        "notes": "Demo prodotto 30 min",
        "createdBy": ADMIN,
    })

    # ── 17. Form submission ─────────────────────────────────────────────────
    await upsert(db, "form_submissions", {
        "_id": FORM,
        "formType": "contact",
        "data": {
            "firstName": "Demo",
            "lastName": "Cliente",
            "email": "demo.cliente@example.com",
            "message": "Vorrei una demo di ZenTratto",
        },
        "leadId": LEAD,
    })

    # ── 18. GDPR consent ────────────────────────────────────────────────────
    await upsert(db, "gdpr_consents", {
        "_id": "demo-gdpr-1",
        "leadId": LEAD,
        "type": "marketing",
        "source": "contact_form",
        "legalBasis": "consent",
        "text": "Acconsento al trattamento per finalità di marketing",
        "grantedBy": LEAD,
        "timestamp": utcnow(),
    })

    # ── 19. Report ──────────────────────────────────────────────────────────
    await upsert(db, "reports", {
        "_id": REPORT,
        "title": "Report pipeline demo",
        "timeRange": "30d",
        "generatedBy": ADMIN,
        "generatedByName": "Fred Admin",
        "data": {
            "totalLeads": 2,
            "activeDeals": 1,
            "pipelineValue": 18000,
            "conversionRate": 25,
        },
    })

    # ── 20. Monitor run ─────────────────────────────────────────────────────
    await upsert(db, "monitor_runs", {
        "_id": "demo-monitor-1",
        "kind": "competitor_monitor",
        "ranAt": utcnow(),
        "competitorCount": 1,
        "okCount": 1,
        "failedCount": 0,
        "changeCount": 1,
    })

    logger.info("Demo seed complete.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
