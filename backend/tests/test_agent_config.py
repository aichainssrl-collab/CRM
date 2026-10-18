"""Configurazione agent — default, persistenza, system prompt."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import agent_config_service as cfg


def test_default_config_includes_goal_and_soul():
    d = cfg.DEFAULT_CONFIG
    assert "Goal" in d["goal"] or "goal" in d["goal"].lower() or "Rispondere" in d["goal"]
    assert d["soul"]
    assert d["rules"]
    assert d["language"] == "it"
    assert "tool" in d["rules"].lower() or "tool" in d["toolsPolicy"].lower()


@pytest.mark.asyncio
async def test_get_agent_config_falls_back_to_defaults():
    with patch("app.services.agent_config_service.db") as mock_db:
        mock_db.__getitem__.return_value.find_one = AsyncMock(return_value=None)
        conf = await cfg.get_agent_config()
    assert conf["source"] == "default"
    assert conf["agentName"] == cfg.DEFAULT_CONFIG["agentName"]
    assert conf["goal"] == cfg.DEFAULT_CONFIG["goal"]


@pytest.mark.asyncio
async def test_update_agent_config_merges_and_stores():
    with patch("app.services.agent_config_service.db") as mock_db:
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value={"_id": "agent_config", "goal": "custom"})
        mock_col.update_one = AsyncMock()
        mock_db.__getitem__.return_value = mock_col

        conf = await cfg.update_agent_config({"goal": "custom", "soul": ""})
    assert conf["goal"] == "custom"
    # campo vuoto → ripristina default
    assert conf["soul"] == cfg.DEFAULT_CONFIG["soul"]
    mock_col.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_build_agent_instructions():
    with patch("app.services.agent_config_service.db") as mock_db:
        mock_db.__getitem__.return_value.find_one = AsyncMock(return_value=None)
        text = await cfg.build_agent_instructions()
    assert "# Goal" in text
    assert "# Carattere" in text
    assert "# Regole operative" in text
    assert cfg.DEFAULT_CONFIG["agentName"] in text
