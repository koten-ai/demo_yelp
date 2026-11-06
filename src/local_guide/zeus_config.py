"""Configure kotenai-zeus-client paths and the beer-sample env contract."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

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


def env_text(name: str) -> str:
    return (os.environ.get(name) or "").strip()


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
    """Resolve a beer auth sentinel.

    The client keeps the file auth_mode whenever ZEUS_URL is set, so callers
    write the value returned here into a temporary config first.
    """
    auth = (raw or "").strip()
    if auth not in _AUTH_MODES:
        auth = env_text(auth) or env_text("ZEUS_AUTH_MODE") or "basic"
    env_auth = env_text("ZEUS_AUTH_MODE")
    if env_text("ZEUS_URL") and env_auth in _AUTH_MODES:
        auth = env_auth
    elif env_auth in _AUTH_MODES and auth not in _AUTH_MODES:
        auth = env_auth
    return auth if auth in _AUTH_MODES else "basic"


def resolve_zeus_config(cfg: dict) -> dict:
    """Return Zeus connection settings. ZEUS_URL overrides the file URL."""
    zeus = cfg.get("zeus")
    if not isinstance(zeus, dict) or not zeus:
        return {}
    resolved = dict(zeus)
    url = env_text("ZEUS_URL")
    if url:
        resolved["url"] = url
    return resolved


def resolve_llm_provider_config(cfg: dict) -> dict:
    """Return the LLM block. Beer shape uses ``llm``; older files use ``llm_provider``."""
    llm_provider = cfg.get("llm_provider")
    if isinstance(llm_provider, dict) and llm_provider:
        return dict(llm_provider)
    llm = cfg.get("llm")
    if isinstance(llm, dict) and llm:
        return dict(llm)
    return {}


def _read_config() -> dict:
    path = PROJECT_ROOT / "config.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config.json is not a JSON object")
    return data


def materialize_client_config() -> Path:
    """Write a temp config with a real auth_mode when ZEUS_URL is set.

    config.json stores ZEUS_AUTH_MODE. The client rejects that sentinel and
    keeps the file auth_mode whenever ZEUS_URL is set, same as beer-sample.
    """
    source = PROJECT_ROOT / "config.json"
    if not env_text("ZEUS_URL"):
        return source
    data = _read_config()
    zeus = data.setdefault("zeus", {})
    settings = data.setdefault("settings", {})
    if not isinstance(zeus, dict):
        zeus = {}
        data["zeus"] = zeus
    if not isinstance(settings, dict):
        settings = {}
        data["settings"] = settings
    zeus["auth_mode"] = resolve_auth_mode(str(zeus.get("auth_mode") or ""))
    if str(zeus.get("username") or "") == "ZEUS_USERNAME":
        zeus["username"] = env_text("ZEUS_USERNAME") or "demo_1"
    if str(settings.get("mode") or "") == "ZEUS_MODE":
        settings["mode"] = env_text("ZEUS_MODE") or "analytics"
    directory = Path(tempfile.mkdtemp(prefix="yelp-config-"))
    path = directory / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _bind_legacy_config_path(path: Path) -> None:
    """Point a v1 loader at the materialized file before it reads config.json."""
    try:
        import zeus_client.constants as constants
    except ImportError:
        return
    constants.CONFIG_PATH = path
    constants.USER_CONFIG_DIR = path.parent
    constants.EXAMPLE_CONFIG_PATH = path.parent / "config.example.json"


def _client_symbol(name: str):
    try:
        import zeus_client
    except ImportError:
        return None
    try:
        return getattr(zeus_client, name)
    except AttributeError:
        return None


async def load_config() -> dict:
    """Resolve sentinels, then let zeus_client.load_config read that file."""
    path = materialize_client_config()
    temp = path.resolve() != (PROJECT_ROOT / "config.json").resolve()
    try:
        _bind_legacy_config_path(path)
        client_load = _client_symbol("load_config")
        if client_load is not None:
            loaded = client_load()
            if hasattr(loaded, "__await__"):
                loaded = await loaded
            if isinstance(loaded, dict):
                return loaded
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    finally:
        if temp:
            path.unlink(missing_ok=True)
            try:
                path.parent.rmdir()
            except OSError:
                pass
