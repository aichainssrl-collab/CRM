"""
Email templates — reusable subject/body blocks for sequences and campaigns.
"""
from typing import Optional
from app.services.db_service import db, new_id, utcnow, _to_dict
import logging

logger = logging.getLogger(__name__)

# Built-in playbook templates (AiChain GTM)
DEFAULT_TEMPLATES = [
    {
        "key": "welcome",
        "name": "Welcome / Playbook",
        "subject": "Ecco il tuo AiChain Playbook",
        "bodyHtml": "<p>Ciao {{firstName}},</p><p>grazie per l'interesse. Trovi il playbook in allegato al messaggio di benvenuto.</p><p>— Team AiChain</p>",
        "category": "nurture",
    },
    {
        "key": "case_study",
        "name": "Case study",
        "subject": "Come un cliente legal ha ridotto del 40% il tempo documentale",
        "bodyHtml": "<p>Ciao {{firstName}},</p><p>ti raccontiamo come {{company}} del settore legale ha automatizzato l'estrazione dati con ZenTratto.</p><p>Vuoi i dettagli?</p>",
        "category": "nurture",
    },
    {
        "key": "cost_of_inaction",
        "name": "Costo dell'inazione",
        "subject": "Quanto costa (davvero) non automatizzare i documenti?",
        "bodyHtml": "<p>Ciao {{firstName}},</p><p>ogni mese il team perde ore su classificazione e ricerca documentale. Ti va di fare due conti insieme?</p>",
        "category": "nurture",
    },
    {
        "key": "demo",
        "name": "Demo",
        "subject": "Prenota una demo di 20 minuti",
        "bodyHtml": "<p>Ciao {{firstName}},</p><p>ti mostriamo ZenTratto e SignSiSure su un caso d'uso reale di {{company}}.</p><p><a href=\"https://aichainsolutions.net/booking\">Prenota la demo</a></p>",
        "category": "conversion",
    },
    {
        "key": "last_call",
        "name": "Last call",
        "subject": "Ultimo contatto prima di chiudere il file",
        "bodyHtml": "<p>Ciao {{firstName}},</p><p>se non è il momento giusto, chiudiamo il file e restiamo a disposizione per il futuro.</p><p>— AiChain Solutions</p>",
        "category": "conversion",
    },
]


async def ensure_defaults(created_by: str = "system") -> int:
    """Insert default templates if the collection is empty. Returns inserted count."""
    count = await db["email_templates"].count_documents({"deletedAt": None})
    if count:
        return 0
    now = utcnow()
    docs = []
    for tpl in DEFAULT_TEMPLATES:
        docs.append(
            {
                "_id": new_id(),
                **tpl,
                "createdBy": created_by,
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            }
        )
    if docs:
        await db["email_templates"].insert_many(docs)
    return len(docs)


async def create_template(data: dict, created_by: str) -> dict:
    now = utcnow()
    doc = {
        "_id": new_id(),
        "key": data.get("key") or "",
        "name": data["name"],
        "subject": data.get("subject", ""),
        "bodyHtml": data.get("bodyHtml", ""),
        "category": data.get("category", "other"),
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["email_templates"].insert_one(doc)
    return _to_dict(doc)


async def list_templates(category: Optional[str] = None) -> list[dict]:
    await ensure_defaults()
    query: dict = {"deletedAt": None}
    if category:
        query["category"] = category
    cursor = db["email_templates"].find(query).sort("name", 1)
    docs = await cursor.to_list(length=100)
    return [_to_dict(d) for d in docs]


async def get_template(template_id: str) -> Optional[dict]:
    doc = await db["email_templates"].find_one({"_id": template_id, "deletedAt": None})
    return _to_dict(doc) if doc else None


async def update_template(template_id: str, data: dict) -> Optional[dict]:
    data["updatedAt"] = utcnow()
    doc = await db["email_templates"].find_one_and_update(
        {"_id": template_id, "deletedAt": None},
        {"$set": data},
        return_document=True,
    )
    return _to_dict(doc) if doc else None


async def delete_template(template_id: str) -> bool:
    now = utcnow()
    result = await db["email_templates"].update_one(
        {"_id": template_id, "deletedAt": None},
        {"$set": {"deletedAt": now, "updatedAt": now}},
    )
    return result.modified_count > 0
