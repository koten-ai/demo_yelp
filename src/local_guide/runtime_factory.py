"""Process-wide ZeusRuntime built from config.json."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from zeus_client.config.models import AUTH_MODES

from local_guide.paths import PROJECT_ROOT

_runtime = None


def _env_text(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def load_env_file() -> None:
    """Load repo .env without overriding Compose or the process, and without expanding ``$``."""
    path = PROJECT_ROOT / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, val = text.split("=", 1)
        key = key.strip()
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in {'"', "'"}:
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val


def apply_config_sentinels(data: dict[str, Any]) -> dict[str, Any]:
    """Replace config.json env-name sentinels. Secrets stay as env names."""
    doc = json.loads(json.dumps(data))
    zeus = doc.setdefault("zeus", {})
    settings = doc.setdefault("settings", {})
    llm = doc.setdefault("llm", {})

    auth = str(zeus.get("auth_mode") or "")
    if auth not in AUTH_MODES:
        named = _env_text(auth) if auth else ""
        auth = named if named in AUTH_MODES else _env_text("ZEUS_AUTH_MODE")
    env_auth = _env_text("ZEUS_AUTH_MODE")
    if env_auth in AUTH_MODES:
        auth = env_auth
    zeus["auth_mode"] = auth if auth in AUTH_MODES else "basic"

    user = str(zeus.get("username") or "")
    if not user or user == "ZEUS_USERNAME":
        zeus["username"] = _env_text("ZEUS_USERNAME") or "demo_1"

    mode = str(settings.get("mode") or "")
    if not mode or mode == "ZEUS_MODE":
        settings["mode"] = _env_text("ZEUS_MODE") or "analytics"

    base = str(llm.get("base_url") or "")
    if not base.startswith("http"):
        llm["base_url"] = _env_text("LLM_BASE_URL") or "https://api.x.ai/v1"
    model = str(llm.get("model") or "")
    if not model or model == "LLM_MODEL":
        llm["model"] = _env_text("LLM_MODEL") or "grok-4.5-latest"
    return doc


def _config_path() -> Path:
    load_env_file()
    raw = json.loads((PROJECT_ROOT / "config.json").read_text(encoding="utf-8"))
    doc = apply_config_sentinels(raw)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix="yelp-config-",
        delete=False,
    )
    try:
        json.dump(doc, handle)
        handle.close()
    except Exception:
        handle.close()
        Path(handle.name).unlink(missing_ok=True)
        raise
    return Path(handle.name)


def build_runtime():
    """Load config.json through ZeusRuntime.from_config and wire the ports."""
    from zeus_client import ZeusRuntime
    from zeus_client.adapters.catalog_fs.store import FsCatalogStore
    from zeus_client.adapters.llm_openai_compatible import OpenAICompatibleLlmClient
    from zeus_client.adapters.zeus_http import HttpxZeusPort
    from zeus_client.adapters.zeus_http.catalog_remote import HttpxCatalogRemote

    config_path = _config_path()
    try:
        rt = ZeusRuntime.from_config(config_path, profile="development")
    finally:
        config_path.unlink(missing_ok=True)
    secrets = rt.services.secrets
    rt.services.zeus = HttpxZeusPort(
        endpoint=rt.config.zeus,
        secrets=secrets,
        journal=rt.journal,
    )
    rt.services.llm = OpenAICompatibleLlmClient(
        config=rt.config.llm,
        secrets=secrets,
        journal=rt.journal,
    )
    chat_dir = Path(rt.config.chat_requests_dir or "data/chat_requests")
    if not chat_dir.is_absolute():
        chat_dir = PROJECT_ROOT / chat_dir
    rt.services.catalog = FsCatalogStore(root=chat_dir)
    rt.services.catalog_remote = HttpxCatalogRemote(
        endpoint=rt.config.zeus,
        secrets=secrets,
    )
    return rt


async def get_runtime():
    global _runtime
    if _runtime is None:
        _runtime = build_runtime()
    return _runtime


async def close_runtime() -> None:
    global _runtime
    rt = _runtime
    _runtime = None
    if rt is not None:
        await rt.aclose()
