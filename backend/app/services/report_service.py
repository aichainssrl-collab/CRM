"""
Report narrative generation — LLM executive summary with deterministic fallback.

Never leaves the EU; uses the same litellm runtime config as the CRM agent.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_SYSTEM = (
    "Sei un analista commerciale senior di AiChain Solutions (Catania, IT). "
    "Scrivi in italiano, tono executive e sobrio. "
    "Rispondi SOLO con JSON valido nel formato: "
    '{"narrative": "stringa con 2-3 paragrafi", '
    '"highlights": ["..."], "risks": ["..."], "actions": ["..."]}. '
    "narrative = sintesi CEO; highlights = 2-4 punti di forza; "
    "risks = 1-3 rischi o criticità; actions = 2-4 azioni consigliate concrete."
)


def _fallback_narrative(report_data: dict[str, Any], time_range: str) -> dict[str, Any]:
    kpis = report_data.get("kpis") or {}
    total = kpis.get("totalLeads") or 0
    new = kpis.get("newLeads") or 0
    active = kpis.get("activeDeals") or 0
    won = kpis.get("wonDeals") or 0
    lost = kpis.get("lostDeals") or 0
    pipeline = float(kpis.get("pipelineValue") or 0)
    revenue = float(kpis.get("revenue") or 0)
    conv = float(kpis.get("conversionRate") or 0)

    narrative = (
        f"Nel periodo {time_range} il CRM conta {total} lead totali, di cui {new} acquisiti di recente. "
        f"La pipeline attiva è di {active} deal per un valore di €{pipeline:,.0f}; "
        f"deal vinti: {won}, persi: {lost}, tasso di conversione {conv:.1f}%. "
        f"I ricavi chiusi ammontano a €{revenue:,.0f}."
    )

    highlights = []
    if new > 0:
        highlights.append(f"{new} nuovi lead nel periodo")
    if pipeline > 0:
        highlights.append(f"Pipeline aperta di €{pipeline:,.0f}")
    if won > 0:
        highlights.append(f"{won} deal vinti (€{revenue:,.0f})")

    risks = []
    if lost > won:
        risks.append("Deal persi superiori a quelli vinti: rivedere il processo di chiusura")
    if total > 0 and conv < 15:
        risks.append(f"Basso tasso di conversione ({conv:.1f}%)")
    if active > 0 and pipeline == 0:
        risks.append("Deal attivi senza valore associato: completare i dati in pipeline")

    actions = []
    if new > 0:
        actions.append("Contattare i nuovi lead entro 48 ore")
    if active > 0:
        actions.append("Aggiornare stage e data di chiusura dei deal attivi")
    actions.append("Pianificare follow-up sulle opportunità più calde")

    return {
        "narrative": narrative,
        "highlights": highlights,
        "risks": risks,
        "actions": actions,
        "source": "fallback",
    }


def _compact_data(report_data: dict[str, Any]) -> dict[str, Any]:
    """Keep only the fields the LLM needs (stay inside prompt budget)."""
    out: dict[str, Any] = {"kpis": report_data.get("kpis") or {}}
    if report_data.get("funnel"):
        out["funnel"] = report_data["funnel"][:10]
    if report_data.get("velocity"):
        out["velocity"] = report_data["velocity"][:10]
    if report_data.get("performance"):
        out["performance"] = report_data["performance"][:8]
    if report_data.get("forecastTotal"):
        out["forecastTotal"] = report_data["forecastTotal"]
    return out


def _parse_llm_json(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    narrative = data.get("narrative") or data.get("summary") or ""
    return {
        "narrative": str(narrative).strip(),
        "highlights": [str(x) for x in (data.get("highlights") or [])][:6],
        "risks": [str(x) for x in (data.get("risks") or [])][:6],
        "actions": [str(x) for x in (data.get("actions") or [])][:6],
        "source": "llm",
    }


async def generate_narrative(
    report_data: dict[str, Any],
    time_range: str = "30d",
) -> dict[str, Any]:
    """
    Build an executive narrative from a report snapshot.

    Always returns {narrative, highlights, risks, actions, source}.
    Falls back to a deterministic summary if LLM is unavailable or fails.
    """
    fallback = _fallback_narrative(report_data, time_range)

    try:
        import litellm

        from app.services.llm_settings_service import get_llm_runtime_config

        cfg = await get_llm_runtime_config()
        litellm.drop_params = True
        prompt = (
            f"Periodo: {time_range}\n"
            f"Dati CRM (JSON):\n{json.dumps(_compact_data(report_data), ensure_ascii=False)}"
        )
        resp = await litellm.acompletion(
            **cfg,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=800,
        )
        content = None
        if isinstance(resp, dict):
            content = ((resp.get("choices") or [{}])[0].get("message") or {}).get("content")
        else:
            try:
                content = resp.choices[0].message.content
            except Exception:
                content = None
        parsed = _parse_llm_json(content or "")
        if parsed and parsed.get("narrative"):
            return parsed
        logger.warning("report narrative: LLM returned unusable JSON, using fallback")
    except Exception as exc:
        logger.warning("report narrative LLM failed: %s", exc)

    return fallback
