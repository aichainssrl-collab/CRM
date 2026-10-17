"""Phase B agent tools — copertura moduli CRM."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import crm_agent_service as a
from app.services import agent_tools_phase_b as b


def test_phase_b_tools_registered():
    names = {t["function"]["name"] for t in a.TOOLS}
    for n in (
        "list_tasks", "complete_task", "search_leads", "list_invoices",
        "list_proposals", "deal_pipeline", "export_csv", "crm_kpi",
    ):
        assert n in names
        assert n in a.TOOL_HANDLERS


def test_parse_list_tasks():
    assert a.parse_command("Mostra i task") == ("list_tasks", {})
    assert a.parse_command("i miei task") == ("list_tasks", {"assignedTo": "me"})


def test_parse_invoices_pipeline():
    assert a.parse_command("Mostra fatture")[0] == "list_invoices"
    assert a.parse_command("pipeline dei deal")[0] == "deal_pipeline"


class _AsyncIter:
    def __init__(self, items):
        self._items = list(items)
        self._i = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._i >= len(self._items):
            raise StopAsyncIteration
        v = self._items[self._i]
        self._i += 1
        return v


@pytest.mark.asyncio
async def test_list_tasks_tool():
    with patch("app.services.agent_tools_phase_b.db") as mock_db:
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.limit.return_value = _AsyncIter([
            {"_id": "t1", "title": "Call", "status": "open", "dueDate": None, "priority": "high", "leadId": "L1"},
        ])
        mock_db.__getitem__.return_value.find = MagicMock(return_value=mock_cursor)
        res = await b._list_tasks({}, "u1")
        assert res["ok"] is True
        assert res["count"] == 1


@pytest.mark.asyncio
async def test_delete_lead_requires_confirm():
    res = await b._delete_lead({"email": "x@y.it"}, "u1")
    assert res["ok"] is False
    assert "confirm" in res["error"].lower()


@pytest.mark.asyncio
async def test_deal_pipeline():
    with patch("app.services.agent_tools_phase_b.db") as mock_db:
        mock_db.__getitem__.return_value.aggregate = MagicMock(
            return_value=_AsyncIter([{"_id": "proposal", "count": 2, "value": 10000}])
        )
        res = await b._deal_pipeline({}, "u1")
        assert res["ok"] is True
        assert res["stages"][0]["stage"] == "proposal"


@pytest.mark.asyncio
async def test_list_invoices_wraps_service():
    with patch("app.services.invoice_service.list_invoices", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            {"id": "i1", "number": "2026/001", "title": "X", "clientName": "Acme", "status": "draft", "total": 100},
        ]
        res = await b._list_invoices({}, "u1")
        assert res["ok"] is True
        assert res["count"] == 1


@pytest.mark.asyncio
async def test_export_csv_stores_artifact():
    with patch("app.services.agent_tools_phase_b.db") as mock_db, \
         patch("app.services.export_service.export_leads_csv", new_callable=AsyncMock) as mock_exp:
        mock_exp.return_value = "email,nome\na@b.it,Mario\n"
        mock_db.__getitem__.return_value.insert_one = AsyncMock()
        res = await b._export_csv({"kind": "leads"}, "u1")
        assert res["ok"] is True
        assert "exportId" in res
        mock_db.__getitem__.return_value.insert_one.assert_awaited_once()
