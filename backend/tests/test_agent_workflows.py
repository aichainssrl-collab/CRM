"""Fase D — workflow inbound, team marketing, MCP-lite."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import agent_workflows as w
from app.services import crm_agent_service as a


def test_phase_d_tools_registered():
    names = {t["function"]["name"] for t in a.TOOLS}
    assert "workflow_inbound_lead" in names
    assert "marketing_content" in names
    assert "marketing_insights" in names
    assert "workflow_inbound_lead" in a.TOOL_HANDLERS


def test_parse_workflow_and_marketing():
    assert a.parse_command("workflow inbound per mario@studio.it")[0] == "workflow_inbound_lead"
    assert a.parse_command("genera contenuto marketing per ZenTratto")[0] == "marketing_content"
    assert a.parse_command("insight marketing")[0] == "marketing_insights"


@pytest.mark.asyncio
async def test_inbound_workflow_orchestrates():
    lead = {"_id": "L1", "email": "x@y.it", "firstName": "Mario", "lastName": "R", "companyName": "Acme"}
    with patch("app.services.agent_workflows.db") as mock_db, \
         patch("app.services.scoring_service.calculate_lead_score", new_callable=AsyncMock, return_value=72), \
         patch("app.services.activity_service.append_activity", new_callable=AsyncMock, return_value={"id": "a1"}):
        mock_db.__getitem__.return_value.find_one = AsyncMock(return_value=lead)
        mock_db.__getitem__.return_value.insert_one = AsyncMock()
        mock_db.__getitem__.return_value.update_one = AsyncMock()

        res = await w.run_inbound_lead_workflow("L1", "u1")
    assert res["ok"] is True
    assert res["score"] == 72
    tools = [s["tool"] for s in res["steps"]]
    assert "calculate_lead_score" in tools
    assert "create_task" in tools
    assert "suggest_deal" in tools


def test_mcp_manifest_shape():
    manifest = w.mcp_tool_manifest(a.TOOLS)
    assert manifest["server"] == "aichain-crm-agent"
    assert len(manifest["tools"]) >= 40
    names = {t["name"] for t in manifest["tools"]}
    assert "create_lead" in names
    assert "workflow_inbound_lead" in names


@pytest.mark.asyncio
async def test_mcp_invoke_workflow():
    lead = {"_id": "L1", "email": "x@y.it", "firstName": "A", "lastName": "B"}
    with patch("app.services.agent_workflows.db") as mock_db, \
         patch("app.services.scoring_service.calculate_lead_score", new_callable=AsyncMock, return_value=10), \
         patch("app.services.activity_service.append_activity", new_callable=AsyncMock, return_value={}), \
         patch("app.services.agent_workflows.run_inbound_lead_workflow", new_callable=AsyncMock) as mock_wf:
        mock_wf.return_value = {"ok": True, "summary": "done", "steps": []}
        mock_db.__getitem__.return_value.find_one = AsyncMock(return_value=lead)
        res = await w.execute_mcp_tool("workflow_inbound_lead", {"leadEmail": "x@y.it"}, "u1")
    assert res["ok"] is True
    mock_wf.assert_awaited_once()


@pytest.mark.asyncio
async def test_marketing_assist_content():
    with patch("app.services.marketing_agent_service.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = {"title": "T", "body": "B"}
        res = await w.marketing_assist("u1", "lancio prodotto", content_type="email", topic="lancio")
    assert res["ok"] is True
    assert res["team"] == "marketing"
    assert res["content"]["title"] == "T"
