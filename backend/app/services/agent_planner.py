"""
Agent planner — decomposizione richieste composte in step tool (Fase F).

Pattern Agno Workflow: se il messaggio contiene più intent, genera un piano
e lo esegue in sequenza (max 4 step).
"""
from __future__ import annotations

import re
from typing import Optional


# segmentatori di intent multipli in IT/EN
_SPLIT_RE = re.compile(
    r"\s+(?:e poi|poi|e infine|infine|inoltre|e anche|and then|then|also)\s+|;\s*",
    re.IGNORECASE,
)


def split_compound(message: str) -> list[str]:
    """Divide «crea lead X e poi crea task Y» in segmenti."""
    parts = [p.strip() for p in _SPLIT_RE.split(message or "") if p.strip()]
    return parts if len(parts) > 1 else []


def plan_message(message: str, parse_fn) -> list[dict]:
    """
    Ritorna lista di step {tool, args} o [] se non pianificabile.
    parse_fn = crm_agent_service.parse_command
    """
    segments = split_compound(message)
    if not segments:
        return []
    steps: list[dict] = []
    for seg in segments[:4]:
        parsed = parse_fn(seg)
        if not parsed:
            return []  # se un pezzo non è interpretabile, non forzare il piano
        name, args = parsed
        steps.append({"tool": name, "args": args, "from": seg})
    return steps


def format_action_summary(steps: list[dict]) -> str:
    """Reply strutturata Cosa ho fatto / Cosa manca / Prossimo passo."""
    done = []
    pending = []
    failed = []
    for s in steps:
        r = s.get("result") or {}
        label = s.get("name") or s.get("tool") or "?"
        if r.get("approvalRequired"):
            pending.append(f"{label} (in attesa di approvazione)")
        elif r.get("ok"):
            done.append(label)
        else:
            failed.append(f"{label}: {r.get('error') or 'errore'}")

    lines = []
    if done:
        lines.append("✅ Cosa ho fatto: " + ", ".join(done))
    if pending:
        lines.append("⏳ Cosa manca: " + ", ".join(pending))
    if failed:
        lines.append("❌ Errori: " + "; ".join(failed))
    if not done and not pending and not failed:
        lines.append("Nessuna azione eseguita.")
    # prossimo passo euristico
    if pending:
        lines.append("➡️ Prossimo passo: approva le azioni in sospeso nel pannello.")
    elif failed:
        lines.append("➡️ Prossimo passo: correggi i parametri e riprova.")
    return "\n".join(lines)
