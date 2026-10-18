"""
CRM Agent API — /api/v1/agent/
"""
import logging

from fastapi import APIRouter, Depends
from typing import Optional
from pydantic import BaseModel, Field

from app.deps import require_sales, require_admin, UserRecord
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


# ── Configurazione agent (goal / soul / rules) ───────────────────────────────

class AgentConfigBody(BaseModel):
    agentName: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    goal: Optional[str] = None
    soul: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None
    rules: Optional[str] = None
    fallbackBehavior: Optional[str] = None
    toolsPolicy: Optional[str] = None


@router.get("/config")
async def get_agent_config(user: UserRecord = Depends(require_sales)):
    from app.services import agent_config_service as cfg

    return await cfg.get_agent_config()


@router.put("/config")
@router.post("/config")
async def update_agent_config(
    body: AgentConfigBody,
    user: UserRecord = Depends(require_admin),
):
    from app.services import agent_config_service as cfg

    data = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    return await cfg.update_agent_config(data)


@router.get("/config/preview")
async def preview_agent_config(user: UserRecord = Depends(require_sales)):
    """System prompt effettivo che l'agent usa."""
    from app.services import agent_config_service as cfg

    return {"instructions": await cfg.build_agent_instructions()}


# ── Skill (stile Claude) ─────────────────────────────────────────────────────

class AgentSkillBody(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    triggers: Optional[list[str]] = None
    body: Optional[str] = None
    isActive: Optional[bool] = None


@router.get("/skills")
async def list_agent_skills(user: UserRecord = Depends(require_sales)):
    from app.services import agent_skills_service as skills

    items = await skills.list_skills(include_inactive=True)
    return {"skills": items}


@router.post("/skills")
async def create_agent_skill(body: AgentSkillBody, user: UserRecord = Depends(require_admin)):
    from app.services import agent_skills_service as skills

    return await skills.create_skill(body.model_dump(exclude_unset=True), user.uid)


@router.patch("/skills/{skill_id}")
async def update_agent_skill(
    skill_id: str,
    body: AgentSkillBody,
    user: UserRecord = Depends(require_admin),
):
    from app.services import agent_skills_service as skills

    doc = await skills.update_skill(skill_id, body.model_dump(exclude_unset=True))
    if not doc:
        return {"ok": False, "error": "Skill non trovata"}
    return doc


@router.delete("/skills/{skill_id}")
async def delete_agent_skill(skill_id: str, user: UserRecord = Depends(require_admin)):
    from app.services import agent_skills_service as skills

    ok = await skills.delete_skill(skill_id)
    return {"ok": ok}


@router.post("/skills/{skill_id}/toggle")
async def toggle_agent_skill(skill_id: str, user: UserRecord = Depends(require_admin)):
    from app.services import agent_skills_service as skills

    skill = await skills.get_skill(skill_id)
    if not skill:
        return {"ok": False, "error": "Skill non trovata"}
    return await skills.update_skill(skill_id, {"isActive": not skill.get("isActive")})


@router.get("/skills/preview")
async def preview_skills(
    q: str = "",
    user: UserRecord = Depends(require_sales),
):
    from app.services import agent_skills_service as skills

    return {"instructions": await skills.skills_prompt_block(q)}


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
