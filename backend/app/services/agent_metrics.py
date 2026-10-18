"""
Agent metrics & health — osservabilità runtime (Fase G).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.db_service import db, utcnow


async def agent_health() -> dict:
    """Stato agent + LLM per monitoring / UI."""
    from app.services.crm_agent_service import _llm_available
    from app.services.llm_settings_service import get_llm_settings

    llm_ok = False
    llm_detail = {}
    try:
        cfg = await get_llm_settings()
        llm_detail = {
            "provider": cfg.get("provider"),
            "model": cfg.get("model"),
            "baseUrl": cfg.get("baseUrl"),
            "apiKeySet": bool(cfg.get("apiKeySet")),
        }
        llm_ok = await _llm_available()
    except Exception as exc:
        llm_detail = {"error": str(exc)}

    # ping leggero al provider (timeout breve)
    ping = {"ok": False, "error": None}
    if llm_ok:
        try:
            import httpx

            base = (llm_detail.get("baseUrl") or "").rstrip("/")
            if base:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    r = await client.get(f"{base}/models")
                    ping = {"ok": r.status_code == 200, "status": r.status_code}
            else:
                ping = {"ok": True, "status": "env-configured"}
        except Exception as exc:
            ping = {"ok": False, "error": str(exc)[:120]}

    pending = await db["agent_approvals"].count_documents({"status": "pending", "deletedAt": None})
    runs_24h = await db["agent_runs"].count_documents({
        "createdAt": {"$gte": utcnow() - timedelta(hours=24)},
        "deletedAt": None,
    })

    return {
        "ok": True,
        "llmAvailable": llm_ok,
        "llm": llm_detail,
        "llmPing": ping,
        "pendingApprovals": pending,
        "runsLast24h": runs_24h,
        "timestamp": utcnow().isoformat(),
    }


async def agent_metrics(days: int = 7) -> dict:
    """Metriche qualità run (mode mix, success rate, latenza)."""
    since = utcnow() - timedelta(days=max(days, 1))
    cursor = db["agent_runs"].find({"createdAt": {"$gte": since}, "deletedAt": None})
    total = ok = 0
    by_mode: dict[str, int] = {}
    durations: list[int] = []
    tool_counts: dict[str, int] = {}
    async for r in cursor:
        total += 1
        if r.get("ok"):
            ok += 1
        mode = r.get("mode") or "unknown"
        by_mode[mode] = by_mode.get(mode, 0) + 1
        if isinstance(r.get("durationMs"), (int, float)):
            durations.append(int(r["durationMs"]))
        for t in r.get("tools") or []:
            tool_counts[t] = tool_counts.get(t, 0) + 1

    durations.sort()
    avg = int(sum(durations) / len(durations)) if durations else 0
    p95 = durations[int(len(durations) * 0.95) - 1] if durations else 0

    top_tools = sorted(tool_counts.items(), key=lambda x: -x[1])[:10]
    return {
        "days": days,
        "totalRuns": total,
        "successRate": round(ok / total * 100, 1) if total else 0.0,
        "byMode": by_mode,
        "avgDurationMs": avg,
        "p95DurationMs": p95,
        "topTools": [{"tool": k, "count": v} for k, v in top_tools],
        "timestamp": utcnow().isoformat(),
    }
