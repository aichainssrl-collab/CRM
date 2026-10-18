"""Skill agent stile Claude."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import agent_skills_service as sk


def test_default_skills_present():
    names = {s["name"] for s in sk.DEFAULT_SKILLS}
    assert "follow-up-sequence" in names
    assert "eu-compliance" in names
    assert all(s["body"] for s in sk.DEFAULT_SKILLS)


def test_match_skills_by_trigger():
    skills = sk.DEFAULT_SKILLS
    matched = sk.match_skills("come gestisco il follow-up dopo la call?", skills)
    assert matched
    assert matched[0]["name"] == "follow-up-sequence"


def test_match_skills_empty_message():
    assert sk.match_skills("", sk.DEFAULT_SKILLS) == []


@pytest.mark.asyncio
async def test_list_skills_seeds_defaults():
    with patch("app.services.agent_skills_service.db") as mock_db:
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value=None)
        mock_col.insert_one = AsyncMock()
        mock_col.find.return_value.sort.return_value.__aiter__ = lambda s: iter([])
        # make async iteration empty
        class _Empty:
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise StopAsyncIteration
        mock_col.find.return_value.sort.return_value = _Empty()
        mock_db.__getitem__.return_value = mock_col
        items = await sk.list_skills()
    assert items == []
    assert mock_col.insert_one.await_count == len(sk.DEFAULT_SKILLS)


@pytest.mark.asyncio
async def test_skills_prompt_block_includes_skill():
    with patch("app.services.agent_skills_service.db") as mock_db:
        mock_col = MagicMock()
        mock_col.find_one = AsyncMock(return_value=None)
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
        docs = []
        for s in sk.DEFAULT_SKILLS:
            d = dict(s)
            d["_id"] = s["name"]
            d["isActive"] = True
            docs.append(d)
        mock_col.find.return_value.sort.return_value = _Items(docs)
        mock_db.__getitem__.return_value = mock_col
        block = await sk.skills_prompt_block("devo fare un follow-up")
    assert "Follow-up" in block or "follow-up" in block.lower()
