"""Search must honor config default_mode + default_base_id (deploy contract)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import AsyncMock

import pytest


@dataclass
class StructuredAgentResponse:
    answer: str
    zeus_data: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def _fake_structured(answer: str = "ok") -> StructuredAgentResponse:
    return StructuredAgentResponse(answer=answer, zeus_data=[], warnings=[])


def _sentinel_config(*, default_mode: str | None, base_id: str | None) -> dict:
    cfg = {
        "zeus": {
            "url": "http://from-file:8080",
            "auth_mode": "ZEUS_AUTH_MODE",
            "username": "demo_1",
            "password_env": "ZEUS_PASSWORD",
        },
        "llm": {
            "base_url": "LLM_BASE_URL",
            "model": "LLM_MODEL",
            "api_key_env": "LLM_API_KEY",
            "api_key": "inline-api-key-do-not-pass",
        },
        "llm_provider": {
            "base_url": "LLM_BASE_URL",
            "api_key": "inline-api-key-do-not-pass",
            "models": ["LLM_MODEL"],
        },
        "settings": {"mode": "ZEUS_MODE"},
        "default_api_version": "v2",
        "default_sample": "yelp-demo",
        "samples": {
            "yelp-demo": {
                "bucket": "yelp-demo",
                "scope": "_default",
                "collection": "_default",
            }
        },
    }
    if default_mode is not None:
        cfg["default_mode"] = default_mode
    if base_id is not None:
        cfg["default_base_id"] = base_id
        cfg["base_catalog_dirs"] = ["/app/base_catalogs"]
    return cfg


def _install_search_fakes(monkeypatch, search_mod, cfg: dict) -> dict:
    captured: dict = {}

    async def fake_run_agent(*args, **kwargs):
        captured["zeus_url"] = args[0]
        captured["base_url"] = args[2]
        captured["api_key"] = args[3]
        captured["model"] = args[4]
        captured["mode"] = args[6] if len(args) > 6 else kwargs.get("mode")
        captured["base_id"] = kwargs.get("base_id")
        captured["base_catalog_dirs"] = kwargs.get("base_catalog_dirs")
        captured["api_key_env"] = kwargs.get("api_key_env")
        return "ok", {"notes": []}, [], {"session_id": "", "round": 0}, _fake_structured()

    async def fake_load_config():
        return cfg

    monkeypatch.setattr(search_mod, "load_config", fake_load_config)
    monkeypatch.setattr(search_mod, "run_agent", fake_run_agent)
    monkeypatch.setattr(search_mod, "persist_chat", AsyncMock())
    monkeypatch.setattr(search_mod, "resolve_zeus_config", lambda raw: raw["zeus"])
    monkeypatch.setattr(
        search_mod,
        "resolve_llm_provider_config",
        lambda raw: raw["llm_provider"],
    )
    monkeypatch.setattr(search_mod, "build_tool_order", lambda _chats: {"v1": [], "v2": []})
    monkeypatch.setattr(search_mod, "zeus_data_to_results", lambda _d: [])
    monkeypatch.setattr(search_mod, "extract_businesses", lambda _t: [])
    monkeypatch.setattr(search_mod, "parse_markdown_answer", lambda _a: None)
    return captured


@pytest.mark.asyncio
async def test_search_passes_analytics_base_id(monkeypatch):
    from local_guide import search as search_mod

    monkeypatch.setenv("LLM_API_KEY", "from-env-llm-key")
    monkeypatch.setenv("ZEUS_URL", "http://from-env:8080")
    monkeypatch.setenv("ZEUS_MODE", "analytics")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("LLM_MODEL", "grok-4.5-latest")
    cfg = _sentinel_config(default_mode="analytics", base_id="base-6.1")
    captured = _install_search_fakes(monkeypatch, search_mod, cfg)

    out = await search_mod._search_async("pizza in Tampa", None, ai_process_result=False)

    assert captured["mode"] == "analytics"
    assert captured["base_id"] == "base-6.1"
    assert captured["base_catalog_dirs"] == [Path("/app/base_catalogs")]
    assert captured["zeus_url"] == "http://from-env:8080"
    assert captured["base_url"] == "https://api.x.ai/v1"
    assert captured["model"] == "grok-4.5-latest"
    assert captured["api_key_env"] == "LLM_API_KEY"
    assert captured["api_key"] == os.environ["LLM_API_KEY"]
    assert captured["api_key"] != "inline-api-key-do-not-pass"
    assert out["mode"] == "analytics"
    assert out["base_id"] == "base-6.1"


@pytest.mark.asyncio
async def test_search_defaults_mode_analytics_when_missing(monkeypatch):
    from local_guide import search as search_mod

    monkeypatch.delenv("ZEUS_MODE", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "from-env-llm-key")
    monkeypatch.setenv("ZEUS_URL", "http://from-env:8080")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("LLM_MODEL", "grok-4.5-latest")
    cfg = _sentinel_config(default_mode=None, base_id=None)
    captured = _install_search_fakes(monkeypatch, search_mod, cfg)

    out = await search_mod._search_async("coffee", None)

    assert captured["mode"] == "analytics"
    assert captured["base_id"] is None
    assert captured["api_key_env"] == "LLM_API_KEY"
    assert captured["api_key"] == "from-env-llm-key"
    assert captured["api_key"] != "inline-api-key-do-not-pass"
    assert captured["base_url"] == "https://api.x.ai/v1"
    assert captured["model"] == "grok-4.5-latest"
    assert out["mode"] == "analytics"
    assert out.get("base_id") is None
