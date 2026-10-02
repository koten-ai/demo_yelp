"""Search must honor config default_mode + default_base_id (deploy contract)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from zeus_client import StructuredAgentResponse


def _fake_structured(answer: str = "ok") -> StructuredAgentResponse:
    return StructuredAgentResponse(answer=answer, zeus_data=[], warnings=[])


@pytest.mark.asyncio
async def test_search_passes_analytics_base_id(monkeypatch):
    from local_guide import search as search_mod

    captured = {}

    async def fake_run_agent(*args, **kwargs):
        captured["mode"] = args[6] if len(args) > 6 else kwargs.get("mode")
        captured["base_id"] = kwargs.get("base_id")
        captured["base_catalog_dirs"] = kwargs.get("base_catalog_dirs")
        captured["chat_req_override"] = kwargs.get("chat_req_override")
        return "ok", {"notes": []}, [], {"session_id": "", "round": 0}, _fake_structured()

    async def fake_load_config():
        return {
            "zeus": {
                "url": "http://zeus:8080",
                "auth_mode": "basic",
                "username": "demo_1",
                "password": "x",
            },
            "llm_provider": {
                "base_url": "https://api.x.ai/v1",
                "api_key": "test-key",
                "models": ["grok-test"],
            },
            "default_api_version": "v2",
            "default_mode": "analytics",
            "default_base_id": "base-6.1",
            "base_catalog_dirs": ["/app/base_catalogs"],
            "default_sample": "yelp-demo",
            "samples": {
                "yelp-demo": {
                    "bucket": "yelp-demo",
                    "scope": "_default",
                    "collection": "_default",
                }
            },
        }

    monkeypatch.setattr(search_mod, "load_config", fake_load_config)
    monkeypatch.setattr(search_mod, "run_agent", fake_run_agent)
    monkeypatch.setattr(search_mod, "persist_chat", AsyncMock())
    monkeypatch.setattr(search_mod, "resolve_zeus_config", lambda cfg: cfg["zeus"])
    monkeypatch.setattr(
        search_mod,
        "resolve_llm_provider_config",
        lambda cfg: cfg["llm_provider"],
    )
    monkeypatch.setattr(search_mod, "build_tool_order", lambda _chats: {"v1": [], "v2": []})
    monkeypatch.setattr(search_mod, "zeus_data_to_results", lambda _d: [])
    monkeypatch.setattr(search_mod, "extract_businesses", lambda _t: [])
    monkeypatch.setattr(search_mod, "parse_markdown_answer", lambda _a: None)

    live = {
        "messages": [{"role": "system", "content": "## SCOPE BRIEF\n\n## MINI-SCHEMA\n"}],
        "verbs": [{"name": "find"}],
    }

    async def fake_fetch(zeus_url, mode, bucket, scope):
        captured["fetched"] = (zeus_url, mode, bucket, scope)
        return live

    monkeypatch.setattr(search_mod, "fetch_search_chat_request", fake_fetch)

    out = await search_mod._search_async("pizza in Tampa", None, ai_process_result=False)

    assert captured["mode"] == "analytics"
    assert captured["base_id"] == "base-6.1"
    assert captured["base_catalog_dirs"] == [Path("/app/base_catalogs")]
    assert captured["chat_req_override"] is live
    assert captured["fetched"][1:] == ("analytics", "yelp-demo", "_default")
    assert out["mode"] == "analytics"
    assert out["base_id"] == "base-6.1"


@pytest.mark.asyncio
async def test_search_defaults_mode_analytics_when_missing(monkeypatch):
    from local_guide import search as search_mod

    captured = {}

    async def fake_run_agent(*args, **kwargs):
        captured["mode"] = args[6] if len(args) > 6 else kwargs.get("mode")
        captured["base_id"] = kwargs.get("base_id")
        captured["chat_req_override"] = kwargs.get("chat_req_override")
        return "ok", {"notes": []}, [], {"session_id": "", "round": 0}, _fake_structured()

    async def fake_load_config():
        return {
            "zeus": {"url": "http://zeus:8080", "auth_mode": "basic"},
            "llm_provider": {
                "base_url": "https://api.x.ai/v1",
                "api_key": "test-key",
                "models": ["grok-test"],
            },
            "default_sample": "yelp-demo",
            "samples": {
                "yelp-demo": {
                    "bucket": "yelp-demo",
                    "scope": "_default",
                    "collection": "_default",
                }
            },
        }

    monkeypatch.setattr(search_mod, "load_config", fake_load_config)
    monkeypatch.setattr(search_mod, "run_agent", fake_run_agent)
    monkeypatch.setattr(search_mod, "persist_chat", AsyncMock())
    monkeypatch.setattr(search_mod, "resolve_zeus_config", lambda cfg: cfg["zeus"])
    monkeypatch.setattr(
        search_mod,
        "resolve_llm_provider_config",
        lambda cfg: cfg["llm_provider"],
    )
    monkeypatch.setattr(search_mod, "build_tool_order", lambda _chats: {"v1": [], "v2": []})
    monkeypatch.setattr(search_mod, "zeus_data_to_results", lambda _d: [])
    monkeypatch.setattr(search_mod, "extract_businesses", lambda _t: [])
    monkeypatch.setattr(search_mod, "parse_markdown_answer", lambda _a: None)

    live = {
        "messages": [{"role": "system", "content": "## SCOPE BRIEF\n\n## MINI-SCHEMA\n"}],
        "verbs": [{"name": "find"}],
    }

    async def fake_fetch(*_args, **_kwargs):
        return live

    monkeypatch.setattr(search_mod, "fetch_search_chat_request", fake_fetch)

    out = await search_mod._search_async("coffee", None)

    assert captured["mode"] == "analytics"
    assert captured["base_id"] is None
    assert captured["chat_req_override"] is live
    assert out["mode"] == "analytics"
    assert out.get("base_id") is None
