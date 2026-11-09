"""ZD-28: beer-shaped env contract, secret-free config, and Compose file rules."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SECRET_FIELDS = frozenset({"password", "api_key", "bearer_token"})


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def _walk_no_secret_fields(obj: object) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            assert key not in _SECRET_FIELDS
            if isinstance(value, str):
                assert not value.startswith("xai-")
                assert not value.startswith("sk-")
            _walk_no_secret_fields(value)
    elif isinstance(obj, list):
        for item in obj:
            _walk_no_secret_fields(item)


def test_committed_config_has_no_secret_fields() -> None:
    config = json.loads(_text("config.json"))
    assert not (ROOT / "config.example.json").exists()
    _walk_no_secret_fields(config)
    assert config["profile"] == "development"
    assert config["client_floor"] == "client-floor-6.1"
    assert config["chat_requests_dir"] == "data/chat_requests"
    assert config["zeus"]["auth_mode"] == "ZEUS_AUTH_MODE"
    assert config["zeus"]["username"] == "ZEUS_USERNAME"
    assert config["zeus"]["password_env"] == "ZEUS_PASSWORD"
    assert "scope_credentials" not in config["zeus"]
    assert "password" not in config["zeus"]
    assert config["settings"]["mode"] == "ZEUS_MODE"
    assert config["settings"]["durable_sessions"] is False
    assert config["llm"]["base_url"] == "LLM_BASE_URL"
    assert config["llm"]["model"] == "LLM_MODEL"
    assert config["llm"]["api_key_env"] == "LLM_API_KEY"
    assert config["llm"]["timeout_s"] == 120
    assert config["session"]["semantic_cache"]["enabled"] is False
    assert config["target"] == {
        "bucket": "yelp-demo",
        "scope": "_default",
        "collection": "_default",
    }
    assert "samples" not in config
    assert "default_base_id" not in config
    ignored = subprocess.run(
        ["git", "check-ignore", "config.json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert ignored.returncode != 0
    env_ignored = subprocess.run(
        ["git", "check-ignore", ".env"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert env_ignored.returncode == 0
    assert ".env" in _text(".gitignore").splitlines()
    assert "config.json" not in _text(".gitignore").splitlines()


def test_env_example_names_and_empty_secrets() -> None:
    example = _text(".env.example")
    assert "ZEUS_URL=http://localhost:8080" in example
    assert "ZEUS_BUCKET=yelp-demo" in example
    assert "ZEUS_SCOPE=_default" in example
    assert "ZEUS_COLLECTION=_default" in example
    assert "ZEUS_MODE=analytics" in example
    assert "ZEUS_AUTH_MODE=basic" in example
    assert "ZEUS_USERNAME=demo_1" in example
    assert "LLM_BASE_URL=https://api.x.ai/v1" in example
    assert "LLM_MODEL=grok-4.5-latest" in example
    assert "HOST=127.0.0.1" in example
    assert "PORT=5000" in example
    assert "# ZEUS_BEARER_TOKEN=" in example
    for line in example.splitlines():
        if line.startswith("ZEUS_PASSWORD="):
            assert line == "ZEUS_PASSWORD="
        if line.startswith("LLM_API_KEY="):
            assert line == "LLM_API_KEY="
        assert not line.startswith("ZEUS_BEARER_TOKEN=")


def test_compose_mounts_env_readonly_and_images_copy_config() -> None:
    compose = _text("docker-compose.yml")
    dockerfile = _text("Dockerfile.backend")
    ignore = _text(".dockerignore")
    assert "./.env:/app/.env:ro" in compose
    assert "http://host.docker.internal:8080" in compose
    assert "env_file:" not in compose
    assert "COUCHBASE_QUERY_URL" in compose
    assert "COUCHBASE_USERNAME" in compose
    assert "COUCHBASE_PASSWORD" in compose
    copy_lines = [line.strip() for line in dockerfile.splitlines() if line.strip().startswith("COPY")]
    assert any(line.endswith("config.json ./") or line.endswith("config.json .") for line in copy_lines)
    assert sum("config.json" in line for line in copy_lines) >= 2
    assert all(".env" not in line for line in copy_lines)
    assert "COPY .env" not in dockerfile
    assert "--no-deps -e ." in dockerfile
    assert "python-dotenv" in dockerfile
    assert "python-dotenv" in _text("pyproject.toml")
    assert not (ROOT / "requirements.txt").exists()
    assert ".env" in ignore or "**/.env" in ignore
    assert "config.json" not in ignore.splitlines()
    assert "**/config.json" not in ignore.splitlines()


def test_dotenv_keeps_dollar_password_and_preset_zeus_url(tmp_path, monkeypatch) -> None:
    password = "pa$$w0rd${DOLLAR}"
    (tmp_path / ".env").write_text(
        "ZEUS_URL=http://localhost:8080\n"
        f"ZEUS_PASSWORD={password}\n"
        "LLM_MODEL=grok-4.5-latest\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("local_guide.zeus_config.PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("ZEUS_URL", "http://preset.example:8080")
    monkeypatch.setenv("DOLLAR", "should-not-expand")
    monkeypatch.delenv("ZEUS_PASSWORD", raising=False)
    monkeypatch.delenv("ZEUS_CLIENT_LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    from local_guide.zeus_config import configure_zeus_client

    configure_zeus_client()
    assert os.environ["ZEUS_URL"] == "http://preset.example:8080"
    assert os.environ["ZEUS_PASSWORD"] == password
    assert os.environ["ZEUS_CLIENT_LLM_MODEL"] == "grok-4.5-latest"
    assert "should-not-expand" not in os.environ["ZEUS_PASSWORD"]


def test_zeus_url_writes_real_auth_mode_before_load(tmp_path, monkeypatch) -> None:
    body = {
        "zeus": {
            "url": "http://localhost:8080",
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
    (tmp_path / "config.json").write_text(json.dumps(body), encoding="utf-8")
    monkeypatch.setattr("local_guide.zeus_config.PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("ZEUS_URL", "http://preset.example:8080")
    monkeypatch.setenv("ZEUS_AUTH_MODE", "basic")
    monkeypatch.setenv("ZEUS_USERNAME", "demo_1")
    monkeypatch.setenv("ZEUS_MODE", "analytics")

    from local_guide.zeus_config import resolve_document

    written = resolve_document(body)
    assert written["zeus"]["auth_mode"] == "basic"
    assert written["zeus"]["username"] == "demo_1"
    assert written["zeus"]["url"] == "http://preset.example:8080"
    assert written["settings"]["mode"] == "analytics"
    assert written["llm"]["api_key_env"] == "LLM_API_KEY"
    assert written["zeus"]["password_env"] == "ZEUS_PASSWORD"
    assert "api_key" not in written["llm"]


def test_sentinels_resolve_when_zeus_url_is_unset(monkeypatch) -> None:
    from local_guide.zeus_config import resolve_document

    monkeypatch.delenv("ZEUS_URL", raising=False)
    monkeypatch.setenv("ZEUS_AUTH_MODE", "basic")
    monkeypatch.setenv("ZEUS_MODE", "analytics")
    written = resolve_document(
        {
            "zeus": {
                "url": "http://localhost:8080",
                "auth_mode": "ZEUS_AUTH_MODE",
                "password": "inline-secret",
            },
            "settings": {"mode": "ZEUS_MODE"},
            "llm": {"base_url": "LLM_BASE_URL", "model": "LLM_MODEL", "api_key": "inline-secret"},
        }
    )
    assert written["zeus"]["url"] == "http://localhost:8080"
    assert written["zeus"]["auth_mode"] == "basic"
    assert "password" not in written["zeus"]
    assert "api_key" not in written["llm"]
    assert written["settings"]["mode"] == "analytics"


def test_resolved_document_ignores_inline_llm_key(monkeypatch) -> None:
    from local_guide.zeus_config import resolve_document

    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("ZEUS_URL", "http://zeus.example:8080")
    monkeypatch.setenv("ZEUS_AUTH_MODE", "basic")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.x.ai/v1")
    monkeypatch.setenv("LLM_MODEL", "grok-4.5-latest")
    monkeypatch.setenv("ZEUS_MODE", "analytics")
    written = resolve_document(
        {
            "zeus": {"url": "http://127.0.0.1:8080", "auth_mode": "ZEUS_AUTH_MODE"},
            "llm": {
                "base_url": "LLM_BASE_URL",
                "model": "LLM_MODEL",
                "api_key_env": "LLM_API_KEY",
                "api_key": "inline-secret",
            },
            "llm_provider": {"api_key": "inline-secret", "models": ["nope"]},
            "settings": {"mode": "ZEUS_MODE", "durable_sessions": True},
        }
    )
    assert os.environ.get("LLM_API_KEY", "") == ""
    assert written["zeus"]["url"] == "http://zeus.example:8080"
    assert written["zeus"]["auth_mode"] == "basic"
    assert written["llm"]["api_key_env"] == "LLM_API_KEY"
    assert written["llm"]["model"] == "grok-4.5-latest"
    assert written["llm"]["base_url"] == "https://api.x.ai/v1"
    assert "api_key" not in written["llm"]
    assert "llm_provider" not in written
    assert written["settings"]["mode"] == "analytics"


def test_couchbase_from_mapping_prefers_env(monkeypatch) -> None:
    from local_guide.detail import CouchbaseQueryConfig

    monkeypatch.setenv("COUCHBASE_QUERY_URL", "http://cb.example:8093")
    monkeypatch.setenv("COUCHBASE_USERNAME", "env-user")
    monkeypatch.setenv("COUCHBASE_PASSWORD", "env-secret")
    cfg = CouchbaseQueryConfig.from_mapping(
        {
            "query_url": "http://file:8093",
            "username": "file-user",
            "password": "file-secret",
        },
        zeus_url="http://zeus:8080",
        allow_host_default=False,
    )
    assert cfg is not None
    assert cfg.query_url == "http://cb.example:8093"
    assert cfg.username == "env-user"
    assert cfg.password == "env-secret"


def test_suggest_returns_without_llm_key(monkeypatch, client) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    seen = {"called": False}

    class _Result:
        def to_dict(self):
            return {
                "query": "pi",
                "results": [{"name": "Pizza Place", "business_id": "biz:1"}],
                "source": "zeus_fts",
            }

    class _Data:
        async def search(self, _query, *, options=None):
            seen["called"] = True
            assert os.environ.get("LLM_API_KEY", "") == ""
            assert options is not None
            return _Result()

    async def fake_runtime():
        return SimpleNamespace(
            config=SimpleNamespace(settings=SimpleNamespace(mode="analytics")),
            data=_Data(),
        )

    monkeypatch.setattr("local_guide.zeus_config.get_runtime", fake_runtime)
    short = client.get("/api/suggest", params={"q": "s"})
    assert short.status_code == 200
    assert short.json()["results"] == []
    assert seen["called"] is False
    longer = client.get("/api/suggest", params={"q": "pi"})
    assert longer.status_code == 200
    assert seen["called"] is True
    assert longer.json()["results"][0]["name"] == "Pizza Place"
