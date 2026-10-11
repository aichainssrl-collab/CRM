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
    """Lightweight connectivity probe — no tokens billed beyond a tiny ping."""
    from fastapi import HTTPException

    try:
        import litellm
        cfg = await llm_settings_service.get_llm_runtime_config()
        litellm.drop_params = True
        resp = await litellm.acompletion(
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            temperature=0,
            **cfg,
        )
        model = (resp.get("model") if isinstance(resp, dict) else None) or cfg.get("model")
        return {"ok": True, "model": model}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}