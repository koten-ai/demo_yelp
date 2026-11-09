"""Ask AI chat-trace: CDN widget, debug query, rewind, and public_trace."""
from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from zeus_client import ClientSettings, DebugBundle, TurnResult, TurnStatus
from zeus_client.api.agent import AgentAPI

ROOT = Path(__file__).resolve().parents[1]

_CDN_TRACE = (
    "https://koten-static-cdn.nyc3.cdn.digitaloceanspaces.com/"
    "zeus_client_chat_trace/latest/zeus_client_chat_trace.js"
)


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_run_turn_accepts_rewind() -> None:
    assert "rewind" in inspect.signature(AgentAPI.run_turn).parameters


def test_page_loads_the_cdn_trace_for_agent_search() -> None:
    from local_guide.chat_trace import TOOL_ORDER

    html = _text("frontend/index.html")
    assert _CDN_TRACE in html
    assert "/static/zeus_client_chat_trace.js" not in html
    config = html.split("window.ZeusTraceConfig", 1)[1].split("</script>", 1)[0]
    assert "http://zeus-dev.local:9091" in config
    assert "toolOrder" in config
    assert "enabled" not in config
    assert "zeusAuthToken" not in html
    assert "password" not in config
    for name in (*TOOL_ORDER["v1"], *TOOL_ORDER["v2"]):
        assert f'"{name}"' in config
    search_src = _text("src/local_guide/search.py")
    assert "_APP_TOOL_ORDER" not in search_src
    assert "debug_enabled" not in search_src


def test_spa_navigations_keep_a_truthy_debug_query() -> None:
    helper = _text("frontend/src/lib/debugQuery.tsx")
    assert "withDebugQuery" in helper
    assert "debugQueryValue" in helper
    assert "useDebugNavigate" in helper
    assert "DebugLink" in helper
    assert "DebugNavLink" in helper
    for token in ("1", "true", "yes", "on"):
        assert f'"{token}"' in helper
    pages = {
        "frontend/src/components/layout/AppShell.tsx": "DebugNavLink",
        "frontend/src/pages/LandingPage.tsx": "useDebugNavigate",
        "frontend/src/pages/ConversationalSearchPage.tsx": "useDebugNavigate",
        "frontend/src/pages/BusinessDetailsPage.tsx": "DebugLink",
        "frontend/src/components/results/BusinessCard.tsx": "DebugLink",
    }
    for rel, marker in pages.items():
        text = _text(rel)
        assert "withDebugQuery" not in text
        assert marker in text


def test_only_ask_ai_posts_search_and_mounts_a_card() -> None:
    chat = _text("frontend/src/pages/ConversationalSearchPage.tsx")
    client = _text("frontend/src/api/client.ts")
    assert "agentSearch" in chat
    assert "appendTraceCard" in chat
    assert "openDebugPanel" in chat
    assert "debugQueryValue" in chat
    assert 'fetch("/api/search"' in client
    assert "ai_process_result" in client
    assert "appendTraceCard" not in client
    assert "appendTraceCard" not in _text("frontend/src/pages/LandingPage.tsx")
    assert "appendTraceCard" not in _text("frontend/src/pages/SearchResultsPage.tsx")
    assert "agentSearch" not in _text("frontend/src/pages/LandingPage.tsx")
    assert "agentSearch" not in _text("frontend/src/pages/SearchResultsPage.tsx")
    local = client.split("export async function search(", 1)[1]
    assert "/api/search" not in local
    assert "appendTraceCard" not in _text("frontend/src/pages/BusinessDetailsPage.tsx")


def test_readme_documents_the_debug_chat_trace() -> None:
    readme = _text("README.md")
    assert "?debug=true" in readme
    assert "lightning toggle" in readme
    assert "zeus_client_chat_trace/latest" in readme
    assert "do not mount a trace card" in readme
    assert "http://zeus-dev.local:9091" in readme


def test_apply_config_sentinels_rewrites_names_and_keeps_password_env(monkeypatch) -> None:
    from local_guide.zeus_config import resolve_document

    monkeypatch.setenv("ZEUS_AUTH_MODE", "basic")
    monkeypatch.setenv("ZEUS_USERNAME", "demo_1")
    monkeypatch.delenv("ZEUS_MODE", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    doc = resolve_document(
        {
            "zeus": {
                "auth_mode": "ZEUS_AUTH_MODE",
                "username": "ZEUS_USERNAME",
                "password_env": "ZEUS_PASSWORD",
            },
            "settings": {"mode": "ZEUS_MODE"},
            "llm": {
                "base_url": "LLM_BASE_URL",
                "model": "LLM_MODEL",
                "api_key_env": "LLM_API_KEY",
            },
        }
    )
    assert doc["zeus"]["auth_mode"] == "basic"
    assert doc["zeus"]["username"] == "demo_1"
    assert doc["zeus"]["password_env"] == "ZEUS_PASSWORD"
    assert doc["settings"]["mode"] == "analytics"
    assert doc["llm"]["base_url"] == "https://api.x.ai/v1"
    assert doc["llm"]["model"] == "grok-4.5-latest"
    assert doc["llm"]["api_key_env"] == "LLM_API_KEY"


def test_debug_query_enabled_uses_the_truthy_set() -> None:
    from local_guide.chat_trace import debug_query_enabled

    assert debug_query_enabled("true") is True
    assert debug_query_enabled("TRUE") is True
    assert debug_query_enabled("1") is True
    assert debug_query_enabled("yes") is True
    assert debug_query_enabled("on") is True
    assert debug_query_enabled(True) is True
    assert debug_query_enabled("false") is False
    assert debug_query_enabled("0") is False
    assert debug_query_enabled("") is False
    assert debug_query_enabled(None) is False
    assert debug_query_enabled("no") is False


def test_trace_payload_merges_notes_and_skips_hops_already_present() -> None:
    from local_guide.chat_trace import trace_payload

    rich = TurnResult(
        answer="x",
        status=TurnStatus.OK,
        structured=None,
        session=None,
        debug=DebugBundle(
            public_trace={
                "hops": [{"name": "search"}],
                "notes": ["kept"],
                "session": {"id": "s"},
            },
            hops=({"name": "find"},),
            notes=("added",),
            detective={"version": 2},
            preferred_req_id="req-1",
        ),
        error=None,
        messages=(),
    )
    trace = trace_payload(rich)
    assert trace["hops"] == [{"name": "search"}]
    assert trace["notes"] == ["kept", "added"]
    assert trace["detective"]["version"] == 2
    assert trace["session"]["id"] == "s"
    assert trace["session"]["preferred_req_id"] == "req-1"

    empty = TurnResult(
        answer="x",
        status=TurnStatus.OK,
        structured=None,
        session=None,
        debug=DebugBundle(
            public_trace={},
            hops=({"name": "find"},),
            detective=None,
            preferred_req_id=None,
        ),
        error=None,
        messages=(),
    )
    filled = trace_payload(empty)
    assert filled["hops"] == [{"name": "find"}]
    assert "detective" not in filled
    assert "session" not in filled


def _pour_turn() -> TurnResult:
    return TurnResult(
        answer="Cafe on Main.",
        status=TurnStatus.OK,
        structured=None,
        session=None,
        debug=DebugBundle(
            turn_id="turn_1",
            session_id="sess-1",
            public_trace={"turn_id": "turn_1"},
            hops=({"name": "find", "result_json": {"rows": [{"name": "Cafe"}]}},),
            notes=("semantic_cache.off",),
            detective={"version": 1, "overview": {"headline": "ok"}},
            preferred_req_id="req-pref",
            req_ids=("req-pref",),
        ),
        error=None,
        messages=({"role": "assistant", "content": "Cafe on Main."},),
    )


def _install(monkeypatch, turn: TurnResult):
    from local_guide import search as search_mod
    from local_guide.chat_store import CHATS

    calls: list[dict] = []

    async def fake_run_turn(message, **kwargs):
        calls.append({"message": message, "kwargs": kwargs})
        return turn

    settings = ClientSettings(
        mode="analytics",
        ai_process_result=False,
        durable_sessions=False,
    )
    target = SimpleNamespace(bucket="yelp-demo", scope="_default", collection="_default")
    runtime = SimpleNamespace(
        config=SimpleNamespace(
            zeus=SimpleNamespace(url="http://zeus:8080"),
            llm=SimpleNamespace(model="grok-4.5-latest", provider="xai"),
            settings=settings,
            target=target,
        ),
        catalog=SimpleNamespace(load_for_turn=AsyncMock(return_value={})),
        agent=SimpleNamespace(run_turn=fake_run_turn),
    )

    async def fake_runtime():
        return runtime

    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr(search_mod, "get_runtime", fake_runtime)
    monkeypatch.setattr(search_mod, "persist_chat", AsyncMock())
    CHATS.clear()
    return search_mod, calls


@pytest.mark.asyncio
async def test_debug_true_search_passes_rewind_and_trace(monkeypatch) -> None:
    search_mod, calls = _install(monkeypatch, _pour_turn())
    out = await search_mod.run_search("coffee", None, rewind=True)
    assert len(calls) == 1
    assert calls[0]["kwargs"]["rewind"] is True
    assert "chat_request" not in calls[0]["kwargs"]
    assert "base_id" not in calls[0]["kwargs"]
    assert calls[0]["kwargs"]["prior_messages"] == ()
    assert out["rewind"] is True
    assert out["trace"]["session"]["preferred_req_id"] == "req-pref"
    assert out["trace"]["detective"]["version"] == 1
    assert "semantic_cache.off" in out["trace"]["notes"]
    assert out["trace"]["hops"][0]["name"] == "find"
    from local_guide.chat_store import CHATS
    from local_guide.chat_trace import TOOL_ORDER

    assert out["chat_id"].startswith("yelp_")
    assert out["chat_id"] not in CHATS
    assert out["target"] == "yelp-demo/_default/_default"
    assert out["mode"] == "analytics"
    assert out["model"] == "grok-4.5-latest"
    assert out["provider"] == "xai"
    assert out["tool_order"]["v1"] == TOOL_ORDER["v1"]
    assert out["tool_order"]["v2"] == TOOL_ORDER["v2"]
    search_mod.persist_chat.assert_not_awaited()


@pytest.mark.asyncio
async def test_omitted_or_false_debug_leaves_rewind_off(monkeypatch) -> None:
    search_mod, calls = _install(monkeypatch, _pour_turn())
    omitted = await search_mod._search_async("porter", None)
    falsey = await search_mod.run_search("wheat", None, rewind=False)
    assert [call["kwargs"]["rewind"] for call in calls] == [False, False]
    assert omitted["rewind"] is False
    assert falsey["rewind"] is False
    assert "trace" in omitted


def test_api_search_maps_debug_to_rewind(monkeypatch, client) -> None:
    captured = {}

    async def fake_search(query, chat_id=None, *, ai_process_result=False, rewind=False):
        captured["rewind"] = rewind
        captured["query"] = query
        return {
            "chat_id": "yelp_dbg",
            "query": query,
            "answer": "ok",
            "results": [],
            "rewind": rewind,
            "trace": {"notes": []},
        }

    monkeypatch.setattr("local_guide.app.run_search", fake_search)
    yes = client.post("/api/search", json={"query": "coffee", "debug": "yes"})
    off = client.post("/api/search", json={"query": "tea", "debug": "false"})
    omitted = client.post("/api/search", json={"query": "parks"})
    turned = client.post("/api/search", json={"query": "parks", "debug": "on"})
    assert yes.status_code == 200
    assert yes.json()["rewind"] is True
    assert off.json()["rewind"] is False
    assert omitted.json()["rewind"] is False
    assert turned.json()["rewind"] is True
    assert captured["rewind"] is True
    assert captured["query"] == "parks"


@pytest.mark.asyncio
async def test_rewind_turn_is_not_reused(monkeypatch) -> None:
    from local_guide.chat_store import CHATS

    search_mod, calls = _install(monkeypatch, _pour_turn())
    first = await search_mod._search_async("lager", "yelp_keep")
    stored = list(CHATS["yelp_keep"]["turns"])
    assert stored
    debug = await search_mod.run_search("lager", "yelp_keep", rewind=True)
    assert debug["rewind"] is True
    assert CHATS["yelp_keep"]["turns"] == stored
    assert calls[1]["kwargs"]["rewind"] is True
    assert calls[1]["kwargs"]["prior_messages"] == ()
    again = await search_mod._search_async("lager", "yelp_keep")
    assert again["rewind"] is False
    assert calls[2]["kwargs"]["rewind"] is False
    assert calls[2]["kwargs"]["prior_messages"] == tuple(stored)
    assert first["chat_id"] == "yelp_keep"


def test_detail_suggest_and_insight_have_no_trace(monkeypatch, client) -> None:
    async def biz(business_id, chat_id=None):
        return {"business": {"name": "Cafe", "business_id": business_id}}

    async def reviews(business_id, limit=20):
        return {"business_id": business_id, "reviews": [], "count": 0, "source": "sample"}

    async def insight(business_id, chat_id=None):
        return {
            "business_id": business_id,
            "summary": "ok",
            "the_good": [],
            "the_bad": [],
            "best_for": [],
            "reviews": [],
        }

    async def suggest(q, limit=8):
        return {"query": q, "results": [], "count": 0, "source": "sample"}

    monkeypatch.setattr("local_guide.app.get_business", biz)
    monkeypatch.setattr("local_guide.app.fetch_business_reviews", reviews)
    monkeypatch.setattr("local_guide.app.run_business_insight", insight)
    monkeypatch.setattr("local_guide.app.run_suggest", suggest)

    detail = client.get("/api/business/biz:1", params={"debug": "true"})
    revs = client.get("/api/business/biz:1/reviews", params={"debug": "yes"})
    ins = client.post("/api/business/biz:1/insight", json={"chat_id": "nope"})
    sug = client.get("/api/suggest", params={"q": "cafe", "debug": "on"})
    for res in (detail, revs, ins, sug):
        assert res.status_code == 200
        body = res.json()
        assert "trace" not in body
        assert "rewind" not in body
        assert "tool_order" not in body

    detail_src = _text("src/local_guide/detail.py")
    suggest_src = _text("src/local_guide/suggest.py")
    assert "rewind=" not in detail_src
    assert "rewind=" not in suggest_src
    assert "run_turn" not in suggest_src
