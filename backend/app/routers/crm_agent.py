"""
CRM Agent API — /api/v1/agent/
"""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.deps import require_sales, UserRecord
from app.services import crm_agent_service

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentRunBody(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AgentToolsBody(BaseModel):
    args: dict = Field(default_factory=dict)


@router.get("/tools")
async def list_tools(user: UserRecord = Depends(require_sales)):
    return {"tools": crm_agent_service.TOOLS}


@router.post("/run")
async def run_agent(body: AgentRunBody, user: UserRecord = Depends(require_sales)):
    try:
        return await crm_agent_service.run_agent(body.message, user.uid)
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
