"""Fase C — governance (HITL/guardrail), memory, evals."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import agent_evals as evals
from app.services import agent_governance as gov
from app.services import agent_memory as mem
from app.services import crm_agent_service as a


# ── Guardrails ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_email_quota_guardrail():
    with patch.object(gov, "count_actions_today", new_callable=AsyncMock, return_value=50):
        ok, reason = await gov.check_business_guardrails("send_email", {"toEmail": "a@b.it"}, "u1", "sales")
        assert ok is False
        assert "Quota" in reason


@pytest.mark.asyncio
async def test_deal_value_requires_approval():
    ok, reason = await gov.check_business_guardrails(
        "create_deal", {"title": "X", "value": 80000}, "u1", "sales"
    )
    assert ok is False
    assert "approvazione" in reason.lower()


@pytest.mark.asyncio
async def test_send_email_requires_confirm_without_flag():
    with patch.object(gov, "check_business_guardrails", new_callable=AsyncMock, return_value=(True, "")):
        assert gov.requires_approval("send_email", {}, "") is True
        assert gov.requires_approval("send_email", {"confirm": True}, "") is False


@pytest.mark.asyncio
async def test_run_tool_blocks_delete_without_confirm():
    with patch.object(gov, "create_approval", new_callable=AsyncMock) as mock_appr, \
         patch.object(gov, "check_business_guardrails", new_callable=AsyncMock, return_value=(True, "")):
        mock_appr.return_value = {"id": "appr1", "tool": "delete_lead", "reason": "x", "status": "pending"}
        res = await a.run_tool("delete_lead", {"email": "x@y.it"}, "u1", user_role="sales")
    assert res.get("approvalRequired") is True
    mock_appr.assert_awaited_once()


# ── Memory ───────────────────────────────────────────────────────────────────

def test_extract_remember_command():
    cmd = mem.maybe_extract_memory_command("ricorda che il cliente Y è sensibile al prezzo")
    assert cmd is not None
    assert "sensibile" in cmd["text"]
    assert cmd["kind"] == "note"


def test_extract_preference_command():
    cmd = mem.maybe_extract_memory_command("preferisco le email formali")
    assert cmd is not None
    assert cmd["kind"] == "preference"


def test_extract_memory_none():
    assert mem.maybe_extract_memory_command("mostra i lead") is None


@pytest.mark.asyncio
async def test_remember_fact_persists():
    with patch("app.services.agent_memory.db") as mock_db:
        mock_col = MagicMock()
        mock_col.insert_one = AsyncMock()
        mock_col.find.return_value.sort.return_value.to_list = AsyncMock(return_value=[])
        mock_db.__getitem__.return_value = mock_col
        fact = await mem.remember_fact("u1", "usare tono formale", "preference")
        assert fact["text"] == "usare tono formale"
        mock_col.insert_one.assert_awaited_once()


# ── Evals (parser regression) ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parser_evals_accuracy():
    report = await evals.run_parser_evals()
    assert report["total"] >= 30
    # soglia qualità: ≥ 90% intent parser corretti
    assert report["accuracy"] >= 90.0, report["failures"]


def test_eval_cases_cover_domains():
    tags = {t for c in evals.EVAL_CASES for t in c.tags}
    for domain in ("lead", "task", "deal", "email", "billing", "ops"):
        assert domain in tags
