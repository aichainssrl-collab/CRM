"""
Audit Log, System Stats, Saved Filters & LLM Settings API — /api/v1/admin/
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from app.deps import require_sales, require_admin, UserRecord
from app.services import audit_service, system_service, saved_filter_service, llm_settings_service

router = APIRouter()


class LlmSettingsBody(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    baseUrl: Optional[str] = None
    apiKey: Optional[str] = None
    clearApiKey: bool = False
    localModel: Optional[str] = None
    localBaseUrl: Optional[str] = None


class SavedFilterCreate(BaseModel):
    name: str
    entityType: str
    filters: dict = {}
    isGlobal: bool = False


class SavedFilterUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[dict] = None


# ── Audit Log ──────────────────────────────────────────────────
@router.get("/audit-log")
async def list_audit_log(
    user_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: UserRecord = Depends(require_admin),
):
    return await audit_service.list_audit_log(
        user_id=user_id, entity_type=entity_type, action=action, limit=limit,
    )


@router.get("/audit-log/stats")
async def audit_stats(
    days: int = Query(30, ge=1, le=365),
    user: UserRecord = Depends(require_admin),
):
    return await audit_service.get_audit_stats(days)


# ── System Stats ──────────────────────────────────────────────
@router.get("/system-stats")
async def system_stats(
    user: UserRecord = Depends(require_admin),
):
    return await system_service.get_system_stats()


# ── Saved Filters ──────────────────────────────────────────────
@router.get("/saved-filters")
async def list_saved_filters(
    entity_type: Optional[str] = Query(None),
    user: UserRecord = Depends(require_sales),
):
    return await saved_filter_service.list_saved_filters(user.uid, entity_type)


@router.post("/saved-filters")
async def create_saved_filter(
    body: SavedFilterCreate,
    user: UserRecord = Depends(require_sales),
):
    return await saved_filter_service.create_saved_filter(user.uid, body.model_dump())


@router.patch("/saved-filters/{filter_id}")
async def update_saved_filter(
    filter_id: str,
    body: SavedFilterUpdate,
    user: UserRecord = Depends(require_sales),
):
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await saved_filter_service.update_saved_filter(filter_id, data)
    return result


@router.delete("/saved-filters/{filter_id}")
async def delete_saved_filter(
    filter_id: str,
    user: UserRecord = Depends(require_sales),
):
    ok = await saved_filter_service.delete_saved_filter(filter_id)
    return {"ok": ok}


# ── LLM Settings (admin) ───────────────────────────────────────
@router.get("/llm-settings")
async def get_llm_settings(user: UserRecord = Depends(require_admin)):
    try:
        return await llm_settings_service.get_llm_settings()
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Errore lettura impostazioni LLM: {exc}")


@router.put("/llm-settings")
@router.post("/llm-settings")
async def update_llm_settings(
    body: LlmSettingsBody,
    user: UserRecord = Depends(require_admin),
):
    from fastapi import HTTPException

    try:
        return await llm_settings_service.update_llm_settings(body.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Errore salvataggio impostazioni LLM: {exc}")


@router.get("/llm-settings/test")
async def test_llm_settings(user: UserRecord = Depends(require_admin)):
    """Ping the saved LLM configuration."""
    return await _probe_llm({})


@router.post("/llm-settings/test")
async def test_llm_settings_draft(
    body: LlmSettingsBody,
    user: UserRecord = Depends(require_admin),
):
    """Ping using form values (not necessarily saved)."""
    return await _probe_llm(body.model_dump())


async def _probe_llm(overrides: dict) -> dict:
    """Lightweight connectivity probe — max_tokens=1 ping."""
    try:
        import litellm

        saved = await llm_settings_service.get_llm_settings()
        doc_overrides = {k: v for k, v in (overrides or {}).items() if v not in (None, "", False)}
        # merge draft fields onto effective settings
        provider = doc_overrides.get("provider") or saved.get("provider")
        model = doc_overrides.get("model") or saved.get("model")
        base_url = doc_overrides.get("baseUrl") or saved.get("baseUrl") or None
        local_model = doc_overrides.get("localModel") or saved.get("localModel")
        local_base = doc_overrides.get("localBaseUrl") or saved.get("localBaseUrl")
        api_key = doc_overrides.get("apiKey")

        if not api_key:
            from app.services.db_service import db
            raw = await db["app_settings"].find_one({"_id": "llm"}) or {}
            api_key = raw.get("apiKey")
        if not api_key:
            from app.config import settings as app_settings
            if (provider or "").lower() == "anthropic":
                api_key = app_settings.ANTHROPIC_API_KEY
            elif (provider or "").lower() == "gemini":
                api_key = app_settings.GEMINI_API_KEY
            else:
                api_key = app_settings.OPENAI_API_KEY

        cfg: dict = {"model": model}
        p = (provider or "openai").lower()
        if p == "ollama":
            cfg["model"] = f"ollama/{local_model or 'qwen3:4b'}"
            cfg["api_base"] = local_base or "http://localhost:11434"
            cfg["api_key"] = "ollama"
        elif p == "anthropic":
            cfg["api_key"] = api_key
            if not str(model).startswith("claude"):
                cfg["model"] = f"anthropic/{model}"
        elif p == "gemini":
            cfg["api_key"] = api_key
            if not str(model).startswith("gemini"):
                cfg["model"] = f"gemini/{model}"
        else:
            if not str(model).count("/"):
                cfg["model"] = f"openai/{model}"
            else:
                cfg["model"] = model
            cfg["api_key"] = api_key or "no-key"
            if base_url:
                cfg["api_base"] = base_url

        litellm.drop_params = True
        resp = await litellm.acompletion(
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            temperature=0,
            **cfg,
        )
        model_out = (resp.get("model") if isinstance(resp, dict) else None) or cfg.get("model")
        return {
            "ok": True,
            "model": model_out,
            "provider": p,
            "baseUrl": base_url or "",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}