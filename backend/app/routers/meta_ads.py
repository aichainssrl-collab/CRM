"""
Meta Ads router — proxy verso Meta Graph API.

Il token rimane server-side; il browser non lo vede mai.
Cache in-memory di 15 minuti per evitare rate-limit Meta.
"""

import time
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
import httpx

from app.config import settings
from app.deps import require_sales, UserRecord

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Cache in-memory semplice (chiave → {data, expires_at}) ────────────────────
_cache: dict[str, dict] = {}
CACHE_TTL_SECONDS = 900  # 15 minuti


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and time.time() < entry["expires_at"]:
        return entry["data"]
    return None


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = {"data": data, "expires_at": time.time() + CACHE_TTL_SECONDS}


# ── Helper Meta Graph API ──────────────────────────────────────────────────────
META_BASE = "https://graph.facebook.com"
DATE_PRESETS = {"7d": "last_7d", "30d": "last_30d", "90d": "last_90d"}

# Metriche insights da richiedere a Meta
INSIGHTS_FIELDS = (
    "spend,impressions,clicks,ctr,cpc,cpm,reach,"
    "actions,action_values,cost_per_action_type"
)

CAMPAIGN_FIELDS = (
    "id,name,status,effective_status,objective,"
    f"insights{{date_start,date_stop,{INSIGHTS_FIELDS}}}"
)


def _meta_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _check_configured() -> tuple[str, str]:
    """Verifica che le credenziali Meta siano configurate, altrimenti 503."""
    token = settings.META_ACCESS_TOKEN
    account = settings.META_AD_ACCOUNT_ID
    if not token or not account:
        raise HTTPException(
            status_code=503,
            detail=(
                "Meta Ads non configurato. "
                "Imposta META_ACCESS_TOKEN e META_AD_ACCOUNT_ID nelle variabili d'ambiente."
            ),
        )
    return token, account


async def _meta_get(url: str, params: dict, token: str) -> dict:
    """Esegue GET verso Meta Graph API e gestisce gli errori."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url, params=params, headers=_meta_headers(token))
    if r.status_code != 200:
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        error = body.get("error", {})
        logger.error("Meta API error %s: %s", r.status_code, error)
        raise HTTPException(
            status_code=502,
            detail=f"Meta API error {r.status_code}: {error.get('message', r.text[:200])}",
        )
    return r.json()


# ── Helpers per elaborare i dati Meta ─────────────────────────────────────────

def _actions_to_dict(actions: list[dict] | None) -> dict[str, float]:
    if not actions:
        return {}
    result = {}
    for a in actions:
        result[a["action_type"]] = float(a.get("value", 0))
    return result


def _parse_insights(raw: dict | None) -> dict:
    """Estrae i campi numerici da un oggetto insights Meta."""
    if not raw:
        return {}
    data = raw.get("data", [])
    if not data:
        return {}
    row = data[0]
    actions = _actions_to_dict(row.get("actions"))
    return {
        "spend": float(row.get("spend", 0)),
        "impressions": int(row.get("impressions", 0)),
        "clicks": int(row.get("clicks", 0)),
        "ctr": round(float(row.get("ctr", 0)), 4),
        "cpc": round(float(row.get("cpc", 0)), 4),
        "cpm": round(float(row.get("cpm", 0)), 4),
        "reach": int(row.get("reach", 0)),
        "conversions": actions.get("offsite_conversion.fb_pixel_purchase", 0)
                       or actions.get("purchase", 0)
                       or actions.get("lead", 0),
        "link_clicks": actions.get("link_click", 0),
        "date_start": row.get("date_start"),
        "date_stop": row.get("date_stop"),
    }


# ── Endpoint: riepilogo account ────────────────────────────────────────────────
@router.get("/summary")
async def get_account_summary(
    date_preset: str = Query("30d", description="7d | 30d | 90d"),
    _: UserRecord = Depends(require_sales),
):
    """
    Metriche aggregate dell'intero ad account per il periodo selezionato.
    Risultato in cache 15 minuti.
    """
    token, account = _check_configured()
    cache_key = f"summary:{account}:{date_preset}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    preset = DATE_PRESETS.get(date_preset, "last_30d")
    url = f"{META_BASE}/{settings.META_API_VERSION}/{account}/insights"
    params = {
        "fields": INSIGHTS_FIELDS,
        "date_preset": preset,
        "level": "account",
        "access_token": token,
    }
    raw = await _meta_get(url, params, token)
    data = raw.get("data", [])
    row = data[0] if data else {}

    actions = _actions_to_dict(row.get("actions"))
    result = {
        "spend": float(row.get("spend", 0)),
        "impressions": int(row.get("impressions", 0)),
        "clicks": int(row.get("clicks", 0)),
        "ctr": round(float(row.get("ctr", 0)), 4),
        "cpc": round(float(row.get("cpc", 0)), 4),
        "cpm": round(float(row.get("cpm", 0)), 4),
        "reach": int(row.get("reach", 0)),
        "conversions": actions.get("offsite_conversion.fb_pixel_purchase", 0)
                       or actions.get("purchase", 0)
                       or actions.get("lead", 0),
        "link_clicks": actions.get("link_click", 0),
        "date_preset": date_preset,
    }
    _cache_set(cache_key, result)
    return result


# ── Endpoint: lista campagne con insights ──────────────────────────────────────
@router.get("/campaigns")
async def get_campaigns(
    date_preset: str = Query("30d", description="7d | 30d | 90d"),
    status: str = Query("ACTIVE,PAUSED", description="Filtro status (es. ACTIVE,PAUSED,ARCHIVED)"),
    _: UserRecord = Depends(require_sales),
):
    """
    Lista campagne con metriche insights aggregate per il periodo selezionato.
    """
    token, account = _check_configured()
    cache_key = f"campaigns:{account}:{date_preset}:{status}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    preset = DATE_PRESETS.get(date_preset, "last_30d")

    # Aggiunge date_preset dentro il parametro insights
    fields = (
        f"id,name,status,effective_status,objective,"
        f"insights.date_preset({preset}){{{INSIGHTS_FIELDS}}}"
    )
    url = f"{META_BASE}/{settings.META_API_VERSION}/{account}/campaigns"
    params = {
        "fields": fields,
        "effective_status": [s.strip() for s in status.split(",")],
        "limit": 50,
        "access_token": token,
    }
    raw = await _meta_get(url, params, token)

    campaigns = []
    for c in raw.get("data", []):
        insights = _parse_insights(c.get("insights"))
        campaigns.append({
            "id": c["id"],
            "name": c["name"],
            "status": c.get("effective_status", c.get("status")),
            "objective": c.get("objective"),
            **insights,
        })

    # Ordina per spesa decrescente
    campaigns.sort(key=lambda x: x.get("spend", 0), reverse=True)

    result = {"campaigns": campaigns, "total": len(campaigns), "date_preset": date_preset}
    _cache_set(cache_key, result)
    return result


# ── Endpoint: trend giornaliero (ultime N campagne attive) ────────────────────
@router.get("/trend")
async def get_spend_trend(
    date_preset: str = Query("30d", description="7d | 30d | 90d"),
    _: UserRecord = Depends(require_sales),
):
    """
    Breakdown giornaliero di spend + clicks per il grafico.
    """
    token, account = _check_configured()
    cache_key = f"trend:{account}:{date_preset}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    preset = DATE_PRESETS.get(date_preset, "last_30d")
    url = f"{META_BASE}/{settings.META_API_VERSION}/{account}/insights"
    params = {
        "fields": "spend,clicks,impressions,reach",
        "date_preset": preset,
        "time_increment": 1,  # breakdown giornaliero
        "level": "account",
        "access_token": token,
    }
    raw = await _meta_get(url, params, token)

    trend = [
        {
            "date": row["date_start"],
            "spend": round(float(row.get("spend", 0)), 2),
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "reach": int(row.get("reach", 0)),
        }
        for row in raw.get("data", [])
    ]
    result = {"trend": trend, "date_preset": date_preset}
    _cache_set(cache_key, result)
    return result


# ── Endpoint: stato configurazione ────────────────────────────────────────────
@router.get("/status")
async def get_meta_status(_: UserRecord = Depends(require_sales)):
    """
    Verifica se Meta Ads è configurato e l'account è raggiungibile.
    Utile per mostrare stato nella UI senza errori 503.
    """
    token = settings.META_ACCESS_TOKEN
    account = settings.META_AD_ACCOUNT_ID

    if not token or not account:
        return {"configured": False, "account_id": None, "account_name": None}

    try:
        url = f"{META_BASE}/{settings.META_API_VERSION}/{account}"
        params = {"fields": "id,name,currency,account_status", "access_token": token}
        raw = await _meta_get(url, params, token)
        return {
            "configured": True,
            "account_id": raw.get("id"),
            "account_name": raw.get("name"),
            "currency": raw.get("currency", "EUR"),
            "account_status": raw.get("account_status"),
        }
    except HTTPException:
        return {"configured": True, "account_id": account, "account_name": None, "error": "Token non valido o account non raggiungibile"}
