"""Search enters the Zeus 2.5 pipeline and keeps secrets in env names."""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from zeus_client import TurnStatus
from zeus_client.config.models import ClientSettings, DataTarget


def _sentinel_config() -> dict:
    return {
        "profile": "development",
        "zeus": {
            "url": "http://from-file:8080",
            "auth_mode": "ZEUS_AUTH_MODE",
            "username": "demo_1",
            "password_env": "ZEUS_PASSWORD",
        },
        "llm": {
            "provider": "xai",
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
        "settings": {
            "mode": "ZEUS_MODE",
            "durable_sessions": False,
            "ai_process_result": False,
            "max_rounds": 12,
        },
        "target": {
            "bucket": "yelp-demo",
            "scope": "_default",
            "collection": "_default",
        },
    }


class _Debug:
    def __init__(self) -> None:
        self.hops = ({"name": "search", "result_json": {"rows": []}},)
        self.session_id = ""
        self.rounds = 0
        self.contract_status = None

    def to_dict(self) -> dict:
        return {
            "notes": [],
            "hops": [dict(hop) for hop in self.hops],
            "session_id": self.session_id,
            "rounds": self.rounds,
            "contract_status": self.contract_status,
        }


class _Result:
    def __init__(self) -> None:
        self.answer = "ok"
        self.status = TurnStatus.OK
        self.debug = _Debug()
        self.messages: list = []
        self.layer_a = None
        self.error = None


def _fake_runtime(settings: ClientSettings):
    return SimpleNamespace(
        config=SimpleNamespace(
            settings=settings,
            target=DataTarget(bucket="yelp-demo", scope="_default", collection="_default"),
            llm=SimpleNamespace(model="grok-4.5-latest", provider="xai"),
            zeus=SimpleNamespace(url="http://from-env:8080"),
        ),
        catalog=SimpleNamespace(load_for_turn=AsyncMock()),
        agent=SimpleNamespace(run_turn=AsyncMock(return_value=_Result())),
    )


def _install_search_fakes(monkeypatch, search_mod, runtime):
    async def fake_get_runtime():
        return runtime

    monkeypatch.setattr(search_mod, "get_runtime", fake_get_runtime)
    monkeypatch.setattr(search_mod, "persist_chat", AsyncMock())
    monkeypatch.setattr(search_mod, "extract_businesses", lambda _t: [])
    monkeypatch.setattr(search_mod, "parse_markdown_answer", lambda _a: None)


def _set_search_env(monkeypatch, *, mode: str | None = "analytics", auth: str = "basic") -> None:
    monkeypatch.setenv("LLM_API_KEY", "from-env-llm-key")
    monkeypatch.setenv("ZEUS_URL", "http://from-env:8080")
    monkeypatch.setenv("ZEUS_AUTH_MODE", auth)
    monkeypatch.setenv("ZEUS_PASSWORD", "env-secret")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("LLM_MODEL", "grok-4.5-latest")
    if mode is None:
        monkeypatch.delenv("ZEUS_MODE", raising=False)
    else:
        monkeypatch.setenv("ZEUS_MODE", mode)


@pytest.mark.asyncio
async def test_search_calls_run_turn_without_frozen_catalog(monkeypatch):
    from local_guide import search as search_mod

    _set_search_env(monkeypatch)
    settings = ClientSettings(
        ai_process_result=False,
        durable_sessions=False,
        max_rounds=12,
        mode="analytics",
    )
    runtime = _fake_runtime(settings)
    _install_search_fakes(monkeypatch, search_mod, runtime)

    out = await search_mod._search_async("pizza in Tampa", None, ai_process_result=False)

    load_args, load_kwargs = runtime.catalog.load_for_turn.await_args
    assert load_args == ("analytics",)
    assert load_kwargs["target"] is runtime.config.target
    message, kwargs = runtime.agent.run_turn.await_args.args[0], runtime.agent.run_turn.await_args.kwargs
    assert message == "pizza in Tampa"
    assert "chat_request" not in kwargs
    assert "base_id" not in kwargs
    assert kwargs["target"] is runtime.config.target
    assert kwargs["model"] == "grok-4.5-latest"
    assert kwargs["enable_sessions"] is False
    assert kwargs["settings"].ai_process_result is False
    assert kwargs["settings"].durable_sessions is False
    assert kwargs["settings"].max_rounds == 12
    assert kwargs["rewind"] is False
    assert out["mode"] == "analytics"
    assert out["rewind"] is False
    assert "base_id" not in out
    assert out["target"] == "yelp-demo/_default/_default"
    assert out["zeus_url"] == "http://from-env:8080"
    assert out["model"] == "grok-4.5-latest"


@pytest.mark.asyncio
async def test_search_defaults_mode_analytics_when_missing(monkeypatch):
    from local_guide import search as search_mod

    _set_search_env(monkeypatch, mode=None)
    settings = ClientSettings(mode="analytics", durable_sessions=False, max_rounds=12)
    runtime = _fake_runtime(settings)
    _install_search_fakes(monkeypatch, search_mod, runtime)

    out = await search_mod._search_async("coffee", None)

    assert runtime.catalog.load_for_turn.await_args.args[0] == "analytics"
    assert "base_id" not in runtime.agent.run_turn.await_args.kwargs
    assert "chat_request" not in runtime.agent.run_turn.await_args.kwargs
    assert runtime.agent.run_turn.await_args.kwargs["rewind"] is False
    assert out["mode"] == "analytics"
    assert out["rewind"] is False
    assert "base_id" not in out
    assert out["target"] == "yelp-demo/_default/_default"


@pytest.mark.asyncio
async def test_search_request_flag_overrides_ai_process_result(monkeypatch):
    from local_guide import search as search_mod

    _set_search_env(monkeypatch)
    settings = ClientSettings(
        ai_process_result=False,
        durable_sessions=False,
        max_rounds=12,
        mode="analytics",
    )
    runtime = _fake_runtime(settings)
    _install_search_fakes(monkeypatch, search_mod, runtime)

    await search_mod._search_async("pizza", None, ai_process_result=True)

    used = runtime.agent.run_turn.await_args.kwargs["settings"]
    assert used.ai_process_result is True
    assert used.durable_sessions is False
    assert used.max_rounds == 12
    assert runtime.agent.run_turn.await_args.kwargs["enable_sessions"] is False


def test_auth_mode_prefers_env_then_file(monkeypatch):
    from local_guide.zeus_config import resolve_document

    monkeypatch.delenv("ZEUS_URL", raising=False)
    monkeypatch.delenv("ZEUS_AUTH_MODE", raising=False)
    file_mode = _sentinel_config()
    file_mode["zeus"]["auth_mode"] = "none"
    assert resolve_document(file_mode)["zeus"]["auth_mode"] == "none"

    monkeypatch.setenv("ZEUS_AUTH_MODE", "basic")
    file_mode["zeus"]["auth_mode"] = "bearer"
    assert resolve_document(file_mode)["zeus"]["auth_mode"] == "basic"


def test_resolved_config_keeps_secrets_in_env_names(monkeypatch):
    from zeus_client.config.loader import config_from_mapping

    from local_guide.zeus_config import resolve_document

    _set_search_env(monkeypatch, mode=None)
    resolved = resolve_document(_sentinel_config())
    assert resolved["zeus"]["auth_mode"] == "basic"
    assert resolved["zeus"]["url"] == "http://from-env:8080"
    assert resolved["zeus"]["password_env"] == "ZEUS_PASSWORD"
    assert "password" not in resolved["zeus"]
    assert "bearer_token" not in resolved["zeus"]
    assert resolved["llm"]["api_key_env"] == "LLM_API_KEY"
    assert "api_key" not in resolved["llm"]
    assert resolved["llm"]["base_url"] == "https://api.x.ai/v1"
    assert resolved["llm"]["model"] == "grok-4.5-latest"
    assert resolved["settings"]["mode"] == "analytics"
    assert resolved["settings"]["durable_sessions"] is False

    cfg = config_from_mapping(resolved)
    assert cfg.zeus.url == "http://from-env:8080"
    assert cfg.zeus.auth_mode == "basic"
    assert cfg.zeus.password_env == "ZEUS_PASSWORD"
    assert cfg.llm.api_key_env == "LLM_API_KEY"
    assert cfg.llm.base_url == "https://api.x.ai/v1"
    assert cfg.llm.model == "grok-4.5-latest"
    assert cfg.settings.mode == "analytics"
    assert cfg.settings.durable_sessions is False
    assert cfg.settings.max_rounds == 12
    assert cfg.settings.ai_process_result is False
    assert cfg.target.bucket == "yelp-demo"
    blob = repr(cfg)
    assert "env-secret" not in blob
    assert "from-env-llm-key" not in blob
    assert "inline-api-key-do-not-pass" not in blob


def test_bearer_token_stays_in_the_environment(monkeypatch):
    from zeus_client.config.loader import config_from_mapping

    from local_guide.zeus_config import resolve_document

    _set_search_env(monkeypatch, auth="bearer")
    monkeypatch.setenv("ZEUS_BEARER_TOKEN", "env-token")
    monkeypatch.delenv("ZEUS_PASSWORD", raising=False)
    resolved = resolve_document(_sentinel_config())
    cfg = config_from_mapping(resolved)

    assert resolved["zeus"]["auth_mode"] == "bearer"
    assert "bearer_token" not in resolved["zeus"]
    assert "password" not in resolved["zeus"]
    assert cfg.zeus.auth_mode == "bearer"
    assert cfg.zeus.token_env in (None, "ZEUS_BEARER_TOKEN")
    assert "env-token" not in repr(cfg)


@pytest.mark.asyncio
async def test_load_config_survives_a_second_call(monkeypatch):
    from local_guide import zeus_config

    monkeypatch.setattr(zeus_config, "_cached", None)
    monkeypatch.setattr(zeus_config, "_cached_token", None)
    first = await zeus_config.load_config()
    second = await zeus_config.load_config()

    assert first is second
    assert second["zeus"]["password_env"] == "ZEUS_PASSWORD"
    assert "password" not in second["zeus"]
    assert "api_key" not in second.get("llm", {})


@pytest.mark.asyncio
async def test_get_runtime_rebuilds_when_the_target_changes(monkeypatch, tmp_path):
    from local_guide import zeus_config

    (tmp_path / "config.json").write_text(json.dumps(_sentinel_config()), encoding="utf-8")
    monkeypatch.setattr(zeus_config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(zeus_config, "_cached", None)
    monkeypatch.setattr(zeus_config, "_cached_token", None)
    monkeypatch.setattr(zeus_config, "_runtime", None)
    monkeypatch.setattr(zeus_config, "_runtime_token", None)
    _set_search_env(monkeypatch)
    for name in (
        "ZEUS_CLIENT_URL",
        "ZEUS_CLIENT_BUCKET",
        "ZEUS_CLIENT_SCOPE",
        "ZEUS_CLIENT_COLLECTION",
        "ZEUS_CLIENT_AUTH_MODE",
        "ZEUS_CLIENT_MODE",
        "ZEUS_CLIENT_LLM_MODEL",
        "ZEUS_CLIENT_LLM_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ZEUS_BUCKET", "yelp-demo")

    first = await zeus_config.get_runtime()
    assert first.config.target.bucket == "yelp-demo"
    monkeypatch.setenv("ZEUS_BUCKET", "other-bucket")
    second = await zeus_config.get_runtime()

    assert second is not first
    assert second.config.target.bucket == "other-bucket"
    assert second.config.zeus.url == "http://from-env:8080"


def test_build_runtime_wires_pipeline_ports(monkeypatch):
    from local_guide.zeus_config import build_runtime, resolve_document

    _set_search_env(monkeypatch)
    rt = build_runtime(resolve_document(_sentinel_config()))

    assert rt.services.zeus is not None
    assert rt.services.llm is not None
    assert rt.services.catalog is not None
    assert rt.services.catalog_remote is not None
    assert rt.config.zeus.password_env == "ZEUS_PASSWORD"
    assert rt.config.llm.api_key_env == "LLM_API_KEY"
    assert rt.config.settings.durable_sessions is False
    assert "env-secret" not in repr(rt.config)
    assert "from-env-llm-key" not in repr(rt.config)
