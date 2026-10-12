"""
Report narrative service — LLM + deterministic fallback.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import report_service


_KPI = {
    "totalLeads": 12,
    "newLeads": 4,
    "wonDeals": 2,
    "lostDeals": 1,
    "activeDeals": 3,
    "pipelineValue": 25000.0,
    "revenue": 8000.0,
    "conversionRate": 66.7,
    "topSources": [{"source": "form", "count": 5}],
}


def test_fallback_narrative_shape():
    result = report_service._fallback_narrative({"kpis": _KPI}, "30d")
    assert result["source"] == "fallback"
    assert "12" in result["narrative"]
    assert "€" in result["narrative"]
    assert isinstance(result["highlights"], list)
    assert isinstance(result["risks"], list)
    assert isinstance(result["actions"], list)


def test_parse_llm_json_fenced():
    text = '```json\n{"narrative": "Andamento positivo.", "highlights": ["h1"], "risks": [], "actions": ["a1"]}\n```'
    parsed = report_service._parse_llm_json(text)
    assert parsed is not None
    assert parsed["narrative"] == "Andamento positivo."
    assert parsed["source"] == "llm"


def test_parse_llm_json_invalid():
    assert report_service._parse_llm_json("not json") is None


def test_generate_narrative_fallback_when_llm_fails():
    import asyncio

    async def _run():
        with patch("litellm.acompletion", side_effect=RuntimeError("no llm")):
            return await report_service.generate_narrative({"kpis": _KPI}, "7d")

    result = asyncio.run(_run())
    assert result["source"] == "fallback"
    assert result["narrative"]


def test_generate_narrative_uses_llm():
    import asyncio

    class FakeMsg:
        content = '{"narrative": "Ottimo trimestre.", "highlights": ["+20%"], "risks": ["ritardi"], "actions": ["follow-up"]}'

    class FakeChoice:
        message = FakeMsg()

    class FakeResp:
        choices = [FakeChoice()]

    async def _run():
        cfg = {"model": "openai/gpt-4o-mini", "api_key": "x"}
        with (
            patch("app.services.llm_settings_service.get_llm_runtime_config", new=AsyncMock(return_value=cfg)),
            patch("litellm.acompletion", new=AsyncMock(return_value=FakeResp())),
        ):
            return await report_service.generate_narrative({"kpis": _KPI}, "30d")

    result = asyncio.run(_run())
    assert result["source"] == "llm"
    assert result["narrative"] == "Ottimo trimestre."
    assert result["actions"] == ["follow-up"]
