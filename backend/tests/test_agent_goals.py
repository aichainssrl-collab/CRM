"""Goal agent — progresso e auto-update su tool riusciti."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import agent_goals_service as g


def test_default_goals():
    keys = {x["key"] for x in g.DEFAULT_GOALS}
    assert "execute_actions" in keys
    assert "drive_followups" in keys
    assert all(x["target"] > 0 for x in g.DEFAULT_GOALS)


def test_tool_impact_maps_core_actions():
    assert "create_lead" in g.TOOL_GOAL_IMPACT
    assert "send_email" in g.TOOL_GOAL_IMPACT
    assert "deals_advanced" in g.TOOL_GOAL_IMPACT["move_deal_stage"]


@pytest.mark.asyncio
async def test_ensure_default_goals_idempotent():
    with patch("app.services.agent_goals_service.db") as mock_db:
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value={"_id": "x"})
        mock_col.insert_one = AsyncMock()
        mock_db.__getitem__.return_value = mock_col
        await g.ensure_default_goals()
    assert mock_col.insert_one.await_count == 0


@pytest.mark.asyncio
async def test_record_tool_success_increments_and_completes():
    with patch("app.services.agent_goals_service.db") as mock_db:
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value={"_id": "seed"})
        mock_col.insert_one = AsyncMock()
        mock_col.update_one = AsyncMock()
        mock_col.find.return_value.to_list = AsyncMock(return_value=[
            {"_id": "g1", "title": "Azioni", "metric": "actions_ok", "progress": 29, "target": 30, "status": "in_progress"},
        ])
        mock_db.__getitem__.return_value = mock_col

        touched = await g.record_tool_success("create_lead", "u1")

    assert touched[0]["status"] == "completed"
    assert touched[0]["progress"] == 30
    mock_col.update_one.assert_awaited()


@pytest.mark.asyncio
async def test_goals_prompt_block_shows_progress():
    with patch("app.services.agent_goals_service.db") as mock_db:
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value={"_id": "s"})
        mock_col.insert_one = AsyncMock()
        class _Items:
            def __init__(self, items):
                self._items = items
            def __aiter__(self):
                return self
            async def __anext__(self):
                if not self._items:
                    raise StopAsyncIteration
                return self._items.pop(0)
        mock_col.find.return_value.sort.return_value = _Items([
            {"_id": "g1", "title": "Rispondere veloce", "metric": "responses_ok",
             "progress": 5, "target": 10, "status": "in_progress"},
        ])
        mock_db.__getitem__.return_value = mock_col
        block = await g.goals_prompt_block()
    assert "Rispondere veloce" in block
    assert "5/10" in block
