"""
CRM Agent API — /api/v1/agent/
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.deps import require_sales, UserRecord
from app.services import crm_agent_service

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
    return await crm_agent_service.run_agent(body.message, user.uid)


@router.post("/tools/{name}")
async def run_tool(
    name: str,
    body: AgentToolsBody,
    user: UserRecord = Depends(require_sales),
):
    result = await crm_agent_service.run_tool(name, body.args, user.uid)
    return {"tool": name, **result}
