"""Fase F — knowledge, planner, follow-up."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import agent_knowledge as k
from app.services import agent_planner as p
from app.services import crm_agent_service as a


# ── Knowledge ────────────────────────────────────────────────────────────────

def test_tokens_and_score():
    qt = k._tokens("email marketing legal")
    assert "email" in qt
    assert k._score(qt, "Email marketing per studi legali") > 0
    assert k._score(qt, "") == 0.0


@pytest.mark.asyncio
async def test_search_knowledge_ranks_results():
    docs = [
        {"_id": "c1", "title": "Email marketing legal", "body": "template per studi legali", "tags": []},
        {"_id": "c2", "title": "Altro", "body": "niente di rilevante", "tags": []},
    ]

    class _Cursor:
        def __init__(self, items):
            self._items = list(items)

        def limit(self, n):
            return _Iter(self._items[:n])

        def sort(self, *a, **k):
            return self

    class _Iter:
        def __init__(self, items):
            self._items = list(items)

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self._items:
                raise StopAsyncIteration
            return self._items.pop(0)

    with patch("app.services.db_service.db") as mock_db:
        mock_db.__getitem__.return_value.find = MagicMock(return_value=_Cursor(docs))
        res = await k.search_knowledge("email marketing legal", kinds=["content"], limit=5)
    assert res["ok"] is True
    assert res["results"][0]["id"] == "c1"


# ── Planner ──────────────────────────────────────────────────────────────────

def test_split_compound_message():
    parts = p.split_compound("crea lead Mario email m@x.it e poi crea task Chiamalo email m@x.it")
    assert len(parts) == 2


def test_plan_message_multi_step():
    steps = p.plan_message(
        "crea lead Mario email m@x.it e poi crea task Chiamalo email m@x.it",
        a.parse_command,
    )
    assert len(steps) == 2
    assert steps[0]["tool"] == "create_lead"
    assert steps[1]["tool"] == "create_task"


def test_plan_message_empty_for_single():
    assert p.plan_message("mostra i lead", a.parse_command) == []


def test_format_action_summary():
    text = p.format_action_summary([
        {"name": "create_lead", "result": {"ok": True}},
        {"name": "send_email", "result": {"approvalRequired": True, "ok": False}},
        {"name": "export_csv", "result": {"ok": False, "error": "quota"}},
    ])
    assert "Cosa ho fatto" in text
    assert "Cosa manca" in text
    assert "Prossimo passo" in text


# ── Tools + parser ───────────────────────────────────────────────────────────

def test_phase_f_tools_registered():
    names = {t["function"]["name"] for t in a.TOOLS}
    assert "search_knowledge" in names
    assert "schedule_followup" in names
    assert "search_knowledge" in a.TOOL_HANDLERS


def test_parse_knowledge_and_followup():
    assert a.parse_command("cerca nel knowledge email marketing")[0] == "search_knowledge"
    assert a.parse_command("crea follow-up su mario@studio.it")[0] == "schedule_followup"


@pytest.mark.asyncio
async def test_schedule_followup_creates_task():
    lead = {"_id": "L1", "email": "x@y.it"}
    with patch("app.services.agent_tools_phase_b.db") as mock_db:
        mock_db.__getitem__.return_value.find_one = AsyncMock(return_value=lead)
        mock_db.__getitem__.return_value.insert_one = AsyncMock()
        mock_db.__getitem__.return_value.update_one = AsyncMock()
        from app.services import agent_tools_phase_b as b

        res = await b._schedule_followup({"leadEmail": "x@y.it"}, "u1")
    assert res["ok"] is True
    assert res["taskId"]
