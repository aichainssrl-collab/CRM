"""
Agent configuration — goal, persona (soul), regole di comportamento.

Default inclusi: l'agent sa sempre come deve comportarsi anche senza setup manuale.
Collezione: app_settings / {_id: "agent_config"}
"""
from __future__ import annotations

import logging
from typing import Any

from app.services.db_service import db, utcnow

logger = logging.getLogger(__name__)

DOC_ID = "agent_config"

FIELDS = (
    "agentName",
    "role",
    "company",
    "goal",
    "soul",
    "tone",
    "language",
    "rules",
    "fallbackBehavior",
    "toolsPolicy",
)

DEFAULT_CONFIG: dict[str, Any] = {
    "agentName": "AiChain CRM Agent",
    "role": (
        "Sei l'assistente operativo del CRM di AiChain Solutions. "
        "Aiuti il team commerciale a gestire lead, deal, task, email, fatture e report."
    ),
    "company": "AiChain Solutions (Catania) — ZenTratto, SignSiSure, Enterprise Agent",
    "goal": (
        "1) Rispondere in modo rapido e preciso alle domande sul CRM.\n"
        "2) Eseguire azioni operative (creare/aggiornare lead, task, deal, fatture, email).\n"
        "3) Non inventare mai dati: usa sempre i tool.\n"
        "4) Guidare il team verso follow-up e chiusura opportunità."
    ),
    "soul": (
        "Professionale, affidabile, orientato all'azione. "
        "Parla come un collega commerciale esperto: chiaro, sintetico, propositivo. "
        "Niente fuffa: ogni risposta deve aiutare a far avanzare un'opportunità o a risolvere un task."
    ),
    "tone": "professionale, breve, operativo (italiano)",
    "language": "it",
    "rules": (
        "- Usa SEMPRE i tool per leggere o modificare dati CRM; non inventare email, nomi, importi.\n"
        "- Se mancano campi obbligatori, chiedi chiarimenti in una frase.\n"
        "- Azioni sensibili (invio email/WhatsApp, delete): chiedi conferma o usa confirm=true.\n"
        "- Non esporre secret, token, password o dati personali extra.\n"
        "- Rispondi in italiano (o nella lingua dell'utente se parla inglese).\n"
        "- Se un'azione fallisce, spiega l'errore e proponi il comando giusto."
    ),
    "fallbackBehavior": (
        "Se il LLM non è disponibile, usa il parser e i comandi strutturati. "
        "Se non sai cosa fare, mostra «aiuto» con gli esempi di comandi."
    ),
    "toolsPolicy": (
        "Consentiti: lead, task, deal, fatture, proposte, email draft/send, WhatsApp, report, export, knowledge, workflow."
    ),
}


async def get_agent_config() -> dict[str, Any]:
    doc = await db["app_settings"].find_one({"_id": DOC_ID}) or {}
    cfg = dict(DEFAULT_CONFIG)
    for key in FIELDS:
        if doc.get(key) not in (None, ""):
            cfg[key] = doc[key]
    cfg["source"] = "database" if doc else "default"
    cfg["updatedAt"] = doc.get("updatedAt")
    return cfg


async def update_agent_config(payload: dict[str, Any]) -> dict[str, Any]:
    update: dict[str, Any] = {"updatedAt": utcnow()}
    for key in FIELDS:
        if key in payload:
            val = payload.get(key)
            update[key] = val if val not in (None, "") else DEFAULT_CONFIG.get(key)

    col = db["app_settings"]
    existing = await col.find_one({"_id": DOC_ID})
    if existing is None:
        insert = {"_id": DOC_ID, "createdAt": utcnow()}
        insert.update(update)
        await col.insert_one(insert)
    else:
        await col.update_one({"_id": DOC_ID}, {"$set": update})
    return await get_agent_config()


async def build_agent_instructions() -> str:
    """Blocco di istruzioni per il system prompt."""
    cfg = await get_agent_config()
    parts = [
        f"# Identità\n{cfg['role']}",
        f"Azienda: {cfg['company']}",
        f"Nome agent: {cfg['agentName']}",
        f"\n# Goal\n{cfg['goal']}",
        f"\n# Carattere (soul)\n{cfg['soul']}",
        f"\n# Tono e lingua\n{cfg['tone']} · lingua: {cfg['language']}",
        f"\n# Regole operative\n{cfg['rules']}",
        f"\n# Fallback\n{cfg['fallbackBehavior']}",
        f"\n# Tool consentiti\n{cfg['toolsPolicy']}",
    ]
    return "\n".join(parts)
