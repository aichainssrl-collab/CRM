"""enqueue_task non deve mai far fallire una richiesta di salvataggio."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils import cloud_tasks


@pytest.mark.asyncio
async def test_enqueue_task_returns_true_without_client():
    with patch.object(cloud_tasks, "tasks_client", None):
        assert await cloud_tasks.enqueue_task("recalculate-score", {"lead_id": "x"}) is True


@pytest.mark.asyncio
async def test_enqueue_task_swallows_create_task_errors():
    mock_client = MagicMock()
    mock_client.queue_path.return_value = "projects/p/locations/l/queues/q"
    mock_client.create_task = AsyncMock(side_effect=RuntimeError("queue missing"))

    with patch.object(cloud_tasks, "tasks_client", mock_client):
        ok = await cloud_tasks.enqueue_task("recalculate-score", {"lead_id": "x"})

    assert ok is False


@pytest.mark.asyncio
async def test_enqueue_task_success_returns_true():
    mock_client = MagicMock()
    mock_client.queue_path.return_value = "projects/p/locations/l/queues/q"
    mock_client.create_task = AsyncMock(return_value={})

    with patch.object(cloud_tasks, "tasks_client", mock_client):
        ok = await cloud_tasks.enqueue_task("enrich-lead", {"lead_id": "x"}, delay_seconds=5)

    assert ok is True
    mock_client.create_task.assert_awaited_once()
