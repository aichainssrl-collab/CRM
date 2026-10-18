"""
CRM Agent API — /api/v1/agent/
"""
import logging

from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel, Field

from app.deps import require_sales, UserRecord
from app.services import crm_agent_service

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentRunBody(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    sessionId: Optional[str] = None


class AgentToolsBody(BaseModel):
    args: dict = Field(default_factory=dict)


@router.get("/tools")
async def list_tools(user: UserRecord = Depends(require_sales)):
    return {"tools": crm_agent_service.TOOLS}


@router.get("/runs")
async def list_agent_runs(
    limit: int = 50,
    user: UserRecord = Depends(require_sales),
):
    """Run history for the current user (admins see all if user_id omitted via flag)."""
    from app.services import agent_session_service as sess

    only_self = user.role != "admin"
    runs = await sess.list_runs(user_id=user.uid if only_self else None, limit=limit)
    return {"runs": runs}


@router.post("/run")
async def run_agent(body: AgentRunBody, user: UserRecord = Depends(require_sales)):
    try:
        return await crm_agent_service.run_agent(
            body.message, user.uid, session_id=body.sessionId, user_role=user.role,
        )
    except Exception as exc:
        # Never surface an opaque 500 to the chat UI
        logger.exception("agent run failed")
        return {
            "ok": False,
            "mode": "error",
            "steps": [],
            "reply": f"Errore interno dell'agente: {exc}",
            "error": str(exc),
        }


class ApprovalDecisionBody(BaseModel):
    approve: bool


@router.get("/approvals")
async def list_approvals(user: UserRecord = Depends(require_sales)):
    from app.services import agent_governance as gov

    only_self = user.role != "admin"
    items = await gov.list_pending_approvals(user.uid if only_self else None)
    return {"approvals": items}


@router.post("/approvals/{approval_id}/decision")
async def decide_approval(
    approval_id: str,
    body: ApprovalDecisionBody,
    user: UserRecord = Depends(require_sales),
):
    from app.services import agent_governance as gov

    doc = await gov.resolve_approval(approval_id, user.uid, body.approve)
    if not doc:
        return {"ok": False, "error": "Richiesta non trovata o già gestita"}

    if not body.approve:
        return {
            "ok": True,
            "status": "rejected",
            "tool": doc.get("tool"),
            "message": "Azione respinta",
        }

    # Approvato → esegui il tool con confirm=true
    tool = doc.get("tool")
    args = dict(doc.get("args") or {})
    args["confirm"] = True
    try:
        result = await crm_agent_service.run_tool(
            tool, args, doc.get("userId") or user.uid, user_role=user.role,
        )
        return {
            "ok": bool(result.get("ok")),
            "status": "approved",
            "tool": tool,
            "args": args,
            "result": result,
            "message": result.get("message") or result.get("error") or "Azione eseguita",
        }
    except Exception as exc:
        logger.exception("approved tool %s failed", tool)
        return {
            "ok": False,
            "status": "approved",
            "tool": tool,
            "error": str(exc),
            "message": f"Approvata ma esecuzione fallita: {exc}",
        }


@router.get("/memory")
async def list_memory(user: UserRecord = Depends(require_sales)):
    from app.services import agent_memory as mem

    facts = await mem.list_facts(user.uid)
    return {"facts": facts}


@router.get("/health")
async def agent_health_endpoint(user: UserRecord = Depends(require_sales)):
    from app.services import agent_metrics as m

    return await m.agent_health()


@router.get("/metrics")
async def agent_metrics_endpoint(
    days: int = 7,
    user: UserRecord = Depends(require_sales),
):
    from app.services import agent_metrics as m

    return await m.agent_metrics(days)


# ── MCP-lite (esposizione tool a client esterni) ─────────────────────────────

@router.get("/mcp/manifest")
async def mcp_manifest(user: UserRecord = Depends(require_sales)):
    from app.services.agent_workflows import mcp_tool_manifest

    return mcp_tool_manifest(crm_agent_service.TOOLS)


class McpInvokeBody(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)


@router.post("/mcp/invoke")
async def mcp_invoke(body: McpInvokeBody, user: UserRecord = Depends(require_sales)):
    from app.services.agent_workflows import execute_mcp_tool

    try:
        result = await execute_mcp_tool(body.name, body.arguments, user.uid, user_role=user.role)
        return {"tool": body.name, **result}
    except Exception as exc:
        logger.exception("mcp invoke failed")
        return {"tool": body.name, "ok": False, "error": str(exc)}


@router.post("/tools/{name}")
async def run_tool(
    name: str,
    body: AgentToolsBody,
    user: UserRecord = Depends(require_sales),
):
    try:
        result = await crm_agent_service.run_tool(name, body.args, user.uid)
        return {"tool": name, **result}
    except Exception as exc:
        logger.exception("agent tool %s failed", name)
        return {"tool": name, "ok": False, "error": str(exc)}
