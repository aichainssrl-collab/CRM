"""
Runtime LLM settings stored in MongoDB (overrides env defaults).

Document: app_settings / { _id: "llm" }
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional

from app.config import settings
from app.services.db_service import db, utcnow, _to_dict

logger = logging.getLogger(__name__)

LLM_DOC_ID = "llm"

# Fields we persist (api_key is write-only — never returned in full)
FIELDS = ("provider", "model", "baseUrl", "apiKey", "localModel", "localBaseUrl")


def _mask_key(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "…" + key[-4:]


async def get_llm_settings() -> dict[str, Any]:
    """Effective settings: env defaults + Mongo overrides."""
    doc = await db["app_settings"].find_one({"_id": LLM_DOC_ID}) or {}
    doc = {k: doc.get(k) for k in FIELDS if doc.get(k) not in (None, "")}

    effective = {
        "provider": doc.get("provider") or settings.LLM_PROVIDER,
        "model": doc.get("model") or settings.LLM_MODEL,
        "baseUrl": doc.get("baseUrl") or settings.LLM_BASE_URL or "",
        "apiKeySet": bool(doc.get("apiKey") or settings.OPENAI_API_KEY),
        "apiKeyMasked": _mask_key(doc.get("apiKey") or settings.OPENAI_API_KEY),
        "localModel": doc.get("localModel") or settings.LLM_LOCAL_MODEL,
        "localBaseUrl": doc.get("localBaseUrl") or settings.LLM_LOCAL_BASE_URL,
        "source": "database" if doc else "env",
    }
    # never leak raw key
    effective["apiKey"] = None
    return effective


async def update_llm_settings(payload: dict[str, Any]) -> dict[str, Any]:
    """Upsert LLM settings. Empty apiKey leaves the stored secret unchanged."""
    update: dict[str, Any] = {"updatedAt": utcnow()}
    for key in ("provider", "model", "baseUrl", "localModel", "localBaseUrl"):
        if key in payload:
            update[key] = (payload.get(key) or None)
    if payload.get("clearApiKey"):
        update["apiKey"] = None
    elif payload.get("apiKey"):
        update["apiKey"] = payload["apiKey"]

    col = db["app_settings"]
    existing = await col.find_one({"_id": LLM_DOC_ID})
    if existing is None:
        doc = {"_id": LLM_DOC_ID, "createdAt": utcnow(), **update}
        # drop Nones except explicit clear
        insert = {"_id": LLM_DOC_ID, "createdAt": utcnow()}
        insert.update({k: v for k, v in update.items() if v is not None or k == "apiKey"})
        await col.insert_one(insert)
    else:
        await col.update_one({"_id": LLM_DOC_ID}, {"$set": update})
    return await get_llm_settings()


async def _resolve_model_id(model: str, base_url: str | None, api_key: str | None) -> str:
    """
    Match a display name («Nemotron 3 Nano 4B») to the API model id
    («nvidia/nemotron-3-nano-4b») on OpenAI-compatible servers.
    Avoids BadRequestError from model names with spaces.
    """
    if not model or " " not in model:
        return model
    try:
        import httpx

        async with httpx.AsyncClient(timeout=4) as client:
            url = f"{(base_url or '').rstrip('/')}/models"
            headers = {"Authorization": f"Bearer {api_key or 'no-key'}"}
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            ids = [m.get("id") for m in (resp.json().get("data") or []) if m.get("id")]
        low = model.lower().strip()
        for i in ids:
            if i.lower() == low:
                return i
        slug = re.sub(r"[^a-z0-9]+", "-", low).strip("-")
        for i in ids:
            il = i.lower()
            if slug in il.replace("/", "-") or il.endswith(slug) or slug in il:
                return i
        for i in ids:
            if i.lower().replace("-", " ") == low or i.lower().replace("_", " ") == low:
                return i
    except Exception:
        logger.debug("model id resolve failed for %r", model, exc_info=True)
    return re.sub(r"\s+", "-", model.strip()).lower()


async def get_llm_runtime_config() -> dict[str, Any]:
    """
    Config for litellm.acompletion — DB overrides win over env.
    Returns the same shape as marketing_agent_service._get_llm_config().
    """
    cfg_src = await get_llm_settings()
    provider = (cfg_src.get("provider") or "openai").lower()
    model = cfg_src.get("model") or settings.LLM_MODEL
    base_url = cfg_src.get("baseUrl") or None
    # raw key from DB if set, else env
    doc = await db["app_settings"].find_one({"_id": LLM_DOC_ID}) or {}
    api_key = doc.get("apiKey") or settings.OPENAI_API_KEY

    # Normalize display names → API ids (LM Studio / Ollama / vLLM)
    if base_url and model and " " in str(model):
        model = await _resolve_model_id(str(model), base_url, api_key)

    config: dict[str, Any] = {"model": model}

    if provider == "openai":
        config["api_key"] = api_key
        if base_url:
            config["api_base"] = base_url
    elif provider == "anthropic":
        config["api_key"] = doc.get("apiKey") or settings.ANTHROPIC_API_KEY
        if not str(model).startswith("claude"):
            config["model"] = f"anthropic/{model}"
    elif provider == "gemini":
        config["api_key"] = doc.get("apiKey") or settings.GEMINI_API_KEY
        if not str(model).startswith("gemini"):
            config["model"] = f"gemini/{model}"
    elif provider == "ollama":
        config["model"] = f"ollama/{cfg_src.get('localModel') or settings.LLM_LOCAL_MODEL}"
        config["api_base"] = cfg_src.get("localBaseUrl") or settings.LLM_LOCAL_BASE_URL
        config["api_key"] = "ollama"
    elif provider == "custom":
        # litellm needs a provider prefix for OpenAI-compatible bases
        if not str(model).count("/"):
            config["model"] = f"openai/{model}"
        else:
            config["model"] = model
        if base_url:
            config["api_base"] = base_url
        config["api_key"] = api_key or "no-key"
    else:
        if not str(model).count("/"):
            config["model"] = f"openai/{model}"
        if base_url:
            config["api_base"] = base_url
        config["api_key"] = api_key

    return config
