"""
Agent skills — skill attivabili come in Claude (nome, descrizione, istruzioni).

Ogni skill è un blocco di know-how che l'agent può usare quando pertinente.
Default seed: skill operative CRM già pronte.
Collezione: agent_skills
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

from app.services.db_service import db, new_id, utcnow

logger = logging.getLogger(__name__)

DEFAULT_SKILLS: list[dict[str, Any]] = [
    {
        "name": "qualification-call",
        "title": "Qualificazione lead",
        "description": "Come impostare una call di qualificazione e cosa chiedere.",
        "category": "sales",
        "triggers": ["qualifica", "qualification", "call di qualificazione", "prima call"],
        "body": (
            "Quando l'utente prepara una call di qualificazione:\n"
            "1. Aggiorna lo stato lead a qualified solo se ci sono budget/timing/authority.\n"
            "2. Crea un task «Call di qualificazione» entro 48h.\n"
            "3. Proponi domande: ruolo decisionale, budget indicativo, timeline, tool attuali, pain point.\n"
            "4. Registra esito in add_activity e valuta se aprire un deal."
        ),
        "isActive": True,
    },
    {
        "name": "follow-up-sequence",
        "title": "Follow-up commerciale",
        "description": "Cadenza di follow-up dopo un primo contatto.",
        "category": "sales",
        "triggers": ["follow-up", "follow up", "richiama", "non risponde"],
        "body": (
            "Per lead non reattivi:\n"
            "1) Day 0: email di ringraziamento + proposta valore (draft_email).\n"
            "2) Day 3: task «Richiamo».\n"
            "3) Day 7: email case study settore (marketing_content).\n"
            "4) Day 14: ultimo contatto o archivia se no interesse.\n"
            "Mai più di 1 email al giorno per lo stesso contatto."
        ),
        "isActive": True,
    },
    {
        "name": "proposal-prep",
        "title": "Preparazione proposta",
        "description": "Checklist prima di inviare una proposta o fattura.",
        "category": "billing",
        "triggers": ["proposta", "preventivo", "offerta", "fattura"],
        "body": (
            "Prima di create_proposal / send:\n"
            "- Verifica dati cliente (nome, email, azienda) via find_lead.\n"
            "- Scegli prodotti da list_products e allinea totali/P.IVA.\n"
            "- Imposta validità offerta e note (supporto, implementazione).\n"
            "- Chiedi conferma prima di send_proposal (HITL).\n"
            "- Dopo accettazione: create_invoice fromProposalId."
        ),
        "isActive": True,
    },
    {
        "name": "inbound-handling",
        "title": "Gestione inbound",
        "description": "Cosa fare quando arriva un lead da form o referral.",
        "category": "ops",
        "triggers": ["inbound", "form", "referral", "nuovo contatto dal sito"],
        "body": (
            "Per lead inbound:\n"
            "1. workflow_inbound_lead (score + task follow-up).\n"
            "2. Risposta entro 1h lavorativa.\n"
            "3. Se score ≥ 60: book_demo proposto.\n"
            "4. Arricchisci (enrich) se mancano azienda/ruolo."
        ),
        "isActive": True,
    },
    {
        "name": "eu-compliance",
        "title": "Compliance UE / GDPR",
        "description": "Regole su privacy, export e cancellazione dati.",
        "category": "compliance",
        "triggers": ["gdpr", "privacy", "cancellare dati", "export dati", "consenso"],
        "body": (
            "- Non esporre dati personali extra in chat.\n"
            "- Export/erase GDPR: solo admin + doppia conferma.\n"
            "- Consensi: append-only (mai sovrascrivere la history).\n"
            "- Preferisci canali già consensati (email di lavoro vs marketing)."
        ),
        "isActive": True,
    },
]


async def ensure_default_skills() -> None:
    """Seed idempotente delle skill default."""
    col = db["agent_skills"]
    for skill in DEFAULT_SKILLS:
        existing = await col.find_one({"name": skill["name"], "deletedAt": None})
        if not existing:
            now = utcnow()
            await col.insert_one({
                "_id": new_id(),
                **skill,
                "isDefault": True,
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            })


async def list_skills(*, include_inactive: bool = True) -> list[dict]:
    await ensure_default_skills()
    query: dict[str, Any] = {"deletedAt": None}
    if not include_inactive:
        query["isActive"] = True
    cursor = db["agent_skills"].find(query).sort("category", 1)
    return [_to_dict(d) async for d in cursor]


async def get_skill(skill_id: str) -> Optional[dict]:
    doc = await db["agent_skills"].find_one({"_id": skill_id, "deletedAt": None})
    return _to_dict(doc)


async def create_skill(data: dict, created_by: str) -> dict:
    now = utcnow()
    name = (data.get("name") or "").strip() or f"skill-{new_id()[:8]}"
    doc = {
        "_id": new_id(),
        "name": name,
        "title": data.get("title") or name,
        "description": data.get("description") or "",
        "category": data.get("category") or "custom",
        "triggers": [t.strip() for t in (data.get("triggers") or []) if t.strip()],
        "body": data.get("body") or "",
        "isActive": bool(data.get("isActive", True)),
        "isDefault": False,
        "createdBy": created_by,
        "createdAt": now,
        "updatedAt": now,
        "deletedAt": None,
    }
    await db["agent_skills"].insert_one(doc)
    return _to_dict(doc)


async def update_skill(skill_id: str, data: dict) -> Optional[dict]:
    allowed = {"title", "description", "category", "triggers", "body", "isActive", "name"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return await get_skill(skill_id)
    updates["updatedAt"] = utcnow()
    doc = await db["agent_skills"].find_one_and_update(
        {"_id": skill_id, "deletedAt": None},
        {"$set": updates},
    )
    return _to_dict(doc) if doc else None


async def delete_skill(skill_id: str) -> bool:
    # le skill default non si eliminano, solo si disattivano
    skill = await get_skill(skill_id)
    if skill and skill.get("isDefault"):
        await update_skill(skill_id, {"isActive": False})
        return True
    res = await db["agent_skills"].update_one(
        {"_id": skill_id, "deletedAt": None},
        {"$set": {"deletedAt": utcnow(), "updatedAt": utcnow()}},
    )
    return res.modified_count > 0


def _to_dict(doc: dict | None) -> dict | None:
    if not doc:
        return None
    d = dict(doc)
    d["id"] = d.pop("_id", None)
    return d


def match_skills(message: str, skills: list[dict], limit: int = 3) -> list[dict]:
    """Skill con trigger presenti nel messaggio (o top category match)."""
    low = (message or "").lower()
    scored = []
    for s in skills:
        if not s.get("isActive", True):
            continue
        score = 0
        for trig in s.get("triggers") or []:
            t = str(trig).lower()
            if t and t in low:
                score += 2
        title_words = re.findall(r"[\wà-ú]{3,}", (s.get("title") or "").lower())
        score += sum(1 for w in title_words if w in low)
        if score > 0:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:limit]]


async def skills_prompt_block(message: str = "") -> str:
    """Istruzioni skill per il system prompt (default + match)."""
    skills = await list_skills(include_inactive=False)
    if not skills:
        return ""
    matched = match_skills(message, skills) if message else []
    use = matched or [s for s in skills if s.get("isDefault")][:3]

    lines = ["# Skill disponibili"]
    for s in use:
        lines.append(f"## {s.get('title') or s.get('name')} [{s.get('category')}]")
        if s.get("description"):
            lines.append(f"{s['description']}")
        lines.append(s.get("body") or "")
    if not matched and skills:
        lines.append(
            "(Nessuna skill specifica per questo messaggio: usa le regole generali. "
            f"Skill installate: {', '.join(s.get('title') or s.get('name') for s in skills)}.)"
        )
    return "\n".join(lines)
