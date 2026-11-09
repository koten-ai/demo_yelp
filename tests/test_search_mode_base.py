"""Agent search calls run_turn. Mode comes from the runtime. base_id stays unset."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from zeus_client import ClientSettings, DebugBundle, TurnResult, TurnStatus


def _turn() -> TurnResult:
    return TurnResult(
        answer="ok",
        status=TurnStatus.OK,
        structured=None,
        session=None,
        debug=DebugBundle(public_trace={"notes": []}, notes=()),
        error=None,
        messages=(),
    )


def _runtime(settings: ClientSettings):
    target = SimpleNamespace(bucket="yelp-demo", scope="_default", collection="_default")
    run_turn = AsyncMock(return_value=_turn())
    return SimpleNamespace(
        config=SimpleNamespace(
            zeus=SimpleNamespace(url="http://zeus:8080"),
            llm=SimpleNamespace(model="grok-test", provider="xai"),
            settings=settings,
            target=target,
        ),
        catalog=SimpleNamespace(load_for_turn=AsyncMock(return_value={})),
        agent=SimpleNamespace(run_turn=run_turn),
    )


@pytest.mark.asyncio
async def test_search_calls_run_turn_in_analytics_mode(monkeypatch):
    from local_guide import search as search_mod

    monkeypatch.setenv("LLM_API_KEY", "test-key")
    settings = ClientSettings(mode="analytics", ai_process_result=False, durable_sessions=False)
    runtime = _runtime(settings)

    async def fake_runtime():
        return runtime

    monkeypatch.setattr(search_mod, "get_runtime", fake_runtime)
    monkeypatch.setattr(search_mod, "persist_chat", AsyncMock())

    out = await search_mod._search_async("pizza in Tampa", None, ai_process_result=False)

    kwargs = runtime.agent.run_turn.await_args.kwargs
    assert kwargs["rewind"] is False
    assert "base_id" not in kwargs
    assert "chat_request" not in kwargs
    assert kwargs["settings"].mode == "analytics"
    assert out["mode"] == "analytics"
    assert out["base_id"] is None
    assert out["rewind"] is False


@pytest.mark.asyncio
async def test_search_defaults_mode_analytics_when_missing(monkeypatch):
    from local_guide import search as search_mod

    monkeypatch.setenv("LLM_API_KEY", "test-key")
    settings = ClientSettings(mode="", ai_process_result=False, durable_sessions=False)
    runtime = _runtime(settings)

    async def fake_runtime():
        return runtime

    monkeypatch.setattr(search_mod, "get_runtime", fake_runtime)
    monkeypatch.setattr(search_mod, "persist_chat", AsyncMock())

    out = await search_mod._search_async("coffee", None)

    assert out["mode"] == "analytics"
    assert out.get("base_id") is None
    assert runtime.agent.run_turn.await_args.kwargs["rewind"] is False
