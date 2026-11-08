"""Configure kotenai-zeus-client paths and the beer-sample env contract."""
from __future__ import annotations

import importlib
import json
import os

from dotenv import load_dotenv

from local_guide.paths import PROJECT_ROOT

# Beer .env names → client loader names. Copy only when the destination is empty.
_CLIENT_ENV_PAIRS = (
    ("ZEUS_URL", "ZEUS_CLIENT_URL"),
    ("ZEUS_AUTH_MODE", "ZEUS_CLIENT_AUTH_MODE"),
    ("ZEUS_USERNAME", "ZEUS_CLIENT_USERNAME"),
    ("ZEUS_USER", "ZEUS_CLIENT_USERNAME"),
    ("ZEUS_BUCKET", "ZEUS_CLIENT_BUCKET"),
    ("ZEUS_SCOPE", "ZEUS_CLIENT_SCOPE"),
    ("ZEUS_COLLECTION", "ZEUS_CLIENT_COLLECTION"),
    ("ZEUS_MODE", "ZEUS_CLIENT_MODE"),
    ("LLM_BASE_URL", "ZEUS_CLIENT_LLM_BASE_URL"),
    ("LLM_MODEL", "ZEUS_CLIENT_LLM_MODEL"),
)

_AUTH_MODES = frozenset({"none", "basic", "bearer", "session", "certificate", "pat", "m2m"})

_cached: dict | None = None
_cache_token: tuple | None = None


def env_text(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def client_symbol(name: str, *, module: str = "zeus_client"):
    """Return a zeus_client attribute, or None when this build does not export it.

    zeus_client 2.x raises AttributeError from ``__getattr__`` for unknown names.
    That is not an ImportError.
    """
    try:
        mod = importlib.import_module(module)
    except ImportError:
        return None
    try:
        return getattr(mod, name)
    except AttributeError:
        return None


def _overlay_client_env() -> None:
    """Map beer .env names onto ZEUS_CLIENT_* when the destination is empty."""
    for src, dst in _CLIENT_ENV_PAIRS:
        val = env_text(src)
        if val and not env_text(dst):
            os.environ[dst] = val


def configure_zeus_client() -> None:
    """Load the repo .env, then set path defaults before the runtime is built.

    Compose injects ZEUS_URL before the process starts. override=False keeps
    that value ahead of the file. interpolate=False leaves a password that
    contains ``$`` unchanged (Compose env_file would expand it).
    """
    load_dotenv(PROJECT_ROOT / ".env", override=False, interpolate=False)
    _overlay_client_env()
    os.environ.setdefault("ZEUS_CLIENT_CONFIG_DIR", str(PROJECT_ROOT))
    chat_dir = str(PROJECT_ROOT / "data" / "chat_requests")
    os.environ.setdefault("ZEUS_CHAT_REQUESTS_DIR", chat_dir)
    os.environ.setdefault("ZEUS_CLIENT_CHAT_REQUESTS_DIR", chat_dir)
    os.environ.setdefault("CHAT_LOG_PATH", str(PROJECT_ROOT / "data" / "chats.jsonl"))


def resolve_auth_mode(raw: str | None) -> str:
    """Resolve a beer auth sentinel to a real mode."""
    auth = (raw or "").strip()
    if auth not in _AUTH_MODES:
        auth = env_text(auth) or env_text("ZEUS_AUTH_MODE") or "basic"
    env_auth = env_text("ZEUS_AUTH_MODE")
    if env_text("ZEUS_URL") and env_auth in _AUTH_MODES:
        auth = env_auth
    elif env_auth in _AUTH_MODES and auth not in _AUTH_MODES:
        auth = env_auth
    return auth if auth in _AUTH_MODES else "basic"


def _llm_base_url(llm: dict, provider: dict) -> str:
    base_url = env_text("LLM_BASE_URL")
    if not base_url:
        raw = str(llm.get("base_url") or provider.get("base_url") or "")
        base_url = "" if raw == "LLM_BASE_URL" else raw
    return (base_url or "https://api.x.ai/v1").rstrip("/")


def _llm_model(llm: dict, provider: dict) -> str:
    model = env_text("LLM_MODEL")
    if model:
        return model
    raw = str(llm.get("model") or "").strip()
    if raw and raw != "LLM_MODEL":
        return raw
    models = provider.get("models") or []
    if models:
        picked = str(models[0]).strip()
        if picked and picked != "LLM_MODEL":
            return picked
    return "grok-4.5-latest"


def _mode(data: dict, settings: dict) -> str:
    env_mode = env_text("ZEUS_MODE")
    if env_mode:
        return env_mode
    raw = str(settings.get("mode") or data.get("default_mode") or "").strip()
    if raw and raw != "ZEUS_MODE":
        return raw
    return "analytics"


def _drop_secret_fields(block: dict) -> None:
    block.pop("password", None)
    block.pop("api_key", None)
    block.pop("bearer_token", None)


def resolve_document(raw: dict) -> dict:
    """Return a copy of config with sentinels replaced and inline secrets removed.

    The committed file keeps names (``ZEUS_AUTH_MODE``, ``LLM_API_KEY``). Callers
    read this object. Nothing writes a temp file or points the client at one.
    """
    if not isinstance(raw, dict):
        return {}
    data = json.loads(json.dumps(raw))
    zeus = data.get("zeus") if isinstance(data.get("zeus"), dict) else {}
    settings = data.get("settings") if isinstance(data.get("settings"), dict) else {}
    llm = data.get("llm") if isinstance(data.get("llm"), dict) else {}
    provider = data.get("llm_provider") if isinstance(data.get("llm_provider"), dict) else {}

    url = env_text("ZEUS_URL") or str(zeus.get("url") or "")
    if url == "ZEUS_URL":
        url = ""
    if url:
        zeus["url"] = url.rstrip("/")
    zeus["auth_mode"] = resolve_auth_mode(str(zeus.get("auth_mode") or ""))
    username = env_text("ZEUS_USERNAME") or str(zeus.get("username") or "")
    if username == "ZEUS_USERNAME":
        username = "demo_1"
    if username:
        zeus["username"] = username
    _drop_secret_fields(zeus)
    creds = zeus.get("scope_credentials")
    if isinstance(creds, dict):
        for entry in creds.values():
            if isinstance(entry, dict):
                entry.pop("password", None)
                entry.pop("bearer_token", None)

    mode = _mode(data, settings)
    settings["mode"] = mode
    if str(data.get("default_mode") or "") in {"", "ZEUS_MODE"}:
        data["default_mode"] = mode

    llm["base_url"] = _llm_base_url(llm, provider)
    llm["model"] = _llm_model(llm, provider)
    llm["api_key_env"] = str(llm.get("api_key_env") or provider.get("api_key_env") or "LLM_API_KEY")
    if not llm.get("provider"):
        llm["provider"] = str(provider.get("label") or "xai")
    _drop_secret_fields(llm)
    _drop_secret_fields(provider)
    if provider:
        provider["base_url"] = llm["base_url"]
        data["llm_provider"] = provider

    target = data.get("target") if isinstance(data.get("target"), dict) else {}
    if env_text("ZEUS_BUCKET"):
        target["bucket"] = env_text("ZEUS_BUCKET")
    if env_text("ZEUS_SCOPE"):
        target["scope"] = env_text("ZEUS_SCOPE")
    if env_text("ZEUS_COLLECTION"):
        target["collection"] = env_text("ZEUS_COLLECTION")
    if target:
        data["target"] = target

    data["zeus"] = zeus
    data["settings"] = settings
    data["llm"] = llm
    return data


def resolve_zeus_config(cfg: dict) -> dict:
    """Return Zeus connection settings from an already resolved document."""
    resolved = resolve_document(cfg)
    zeus = resolved.get("zeus")
    return dict(zeus) if isinstance(zeus, dict) else {}


def resolve_llm_provider_config(cfg: dict) -> dict:
    """Return the resolved LLM block. Beer shape uses ``llm``."""
    resolved = resolve_document(cfg)
    llm = resolved.get("llm")
    return dict(llm) if isinstance(llm, dict) else {}


def _read_config() -> dict:
    path = PROJECT_ROOT / "config.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config.json is not a JSON object")
    return data


def _cache_token() -> tuple:
    path = PROJECT_ROOT / "config.json"
    mtime = path.stat().st_mtime_ns if path.is_file() else 0
    return (
        str(PROJECT_ROOT),
        mtime,
        env_text("ZEUS_URL"),
        env_text("ZEUS_AUTH_MODE"),
        env_text("ZEUS_USERNAME"),
        env_text("ZEUS_MODE"),
        env_text("LLM_BASE_URL"),
        env_text("LLM_MODEL"),
        env_text("ZEUS_BUCKET"),
        env_text("ZEUS_SCOPE"),
        env_text("ZEUS_COLLECTION"),
    )


async def load_config() -> dict:
    """Resolve config.json once per process for the current env and file."""
    global _cached, _cache_token
    token = _cache_token()
    if _cached is not None and token == _cache_token:
        return _cached
    resolved = resolve_document(_read_config())
    _cached = resolved
    _cache_token = token
    return resolved
