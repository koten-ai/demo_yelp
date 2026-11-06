"""Search that puts the live yelp-demo chat request on the Zeus turn.

The session create body is ``chat_request``. Omitting it, or sending the
unbound base catalog, is what left search without a scope brief. This path
GETs ``/v1/ai/chat_request.json?scope=yelp-demo/_default`` and passes that
document into ``rt.agent.run_turn``.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from zeus_client import (
    ClientSettings,
    DataTarget,
    RuntimeConfig,
    TurnStatus,
    ZeusRuntime,
    user_facing_answer,
)
from zeus_client.config.models import LlmProviderConfig, ZeusEndpointConfig
from zeus_client.adapters.llm_openai_compatible import OpenAICompatibleLlmClient
from zeus_client.adapters.zeus_http import HttpxZeusPort
from zeus_client.adapters.zeus_http.catalog_remote import HttpxCatalogRemote
from zeus_client.domain.errors import ZeusClientError

from local_guide.paths import PROJECT_ROOT
from local_guide.results_parser import zeus_data_to_results
from local_guide.zeus_config import env_text, resolve_auth_mode

_BUCKET = "yelp-demo"
_SCOPE = "_default"
_MODE = "analytics"
_runtime: ZeusRuntime | None = None


def _read_app_config() -> dict[str, Any]:
    path = PROJECT_ROOT / "config.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _ensure_llm_key(cfg: dict[str, Any]) -> None:
    """Require an LLM key from the environment. Never copy a JSON api_key."""
    del cfg
    if env_text("LLM_API_KEY") or env_text("XAI_API_KEY") or env_text("OPENAI_API_KEY"):
        return
    raise ValueError("LLM_API_KEY is not set. Put it in the environment before search.")


def _runtime_config(cfg: dict[str, Any]) -> RuntimeConfig:
    zeus = cfg.get("zeus") if isinstance(cfg.get("zeus"), dict) else {}
    provider = cfg.get("llm_provider") if isinstance(cfg.get("llm_provider"), dict) else {}
    llm = cfg.get("llm") if isinstance(cfg.get("llm"), dict) else {}
    settings_raw = cfg.get("settings") if isinstance(cfg.get("settings"), dict) else {}
    target = cfg.get("target") if isinstance(cfg.get("target"), dict) else {}

    url = (env_text("ZEUS_URL") or str(zeus.get("url") or "http://localhost:8080")).rstrip("/")
    auth_mode = resolve_auth_mode(str(zeus.get("auth_mode") or ""))
    username = env_text("ZEUS_USERNAME") or str(zeus.get("username") or "")
    if username == "ZEUS_USERNAME":
        username = "demo_1"
    password_env = str(zeus.get("password_env") or "ZEUS_PASSWORD")

    base_url = env_text("LLM_BASE_URL")
    if not base_url:
        raw_base = str(llm.get("base_url") or provider.get("base_url") or "")
        base_url = "https://api.x.ai/v1" if not raw_base or raw_base == "LLM_BASE_URL" else raw_base
    base_url = base_url.rstrip("/")

    model = env_text("LLM_MODEL")
    if not model:
        raw_model = str(llm.get("model") or "").strip()
        if raw_model and raw_model != "LLM_MODEL":
            model = raw_model
    if not model:
        models = provider.get("models") if isinstance(provider.get("models"), list) else []
        picked = str(models[0]).strip() if models else ""
        model = picked if picked and picked != "LLM_MODEL" else "grok-4.5-latest"

    mode = env_text("ZEUS_MODE")
    if not mode:
        raw_mode = str(settings_raw.get("mode") or cfg.get("default_mode") or _MODE).strip()
        mode = _MODE if not raw_mode or raw_mode == "ZEUS_MODE" else raw_mode

    api_key_env = str(llm.get("api_key_env") or "LLM_API_KEY")
    bucket = str(target.get("bucket") or _BUCKET)
    scope = str(target.get("scope") or _SCOPE)
    collection = str(target.get("collection") or "_default")
    durable = settings_raw.get("durable_sessions")
    if not isinstance(durable, bool):
        durable = True

    return RuntimeConfig(
        profile=str(cfg.get("profile") or "development"),
        client_floor=str(cfg.get("client_floor") or "client-floor-6.1"),
        chat_requests_dir=str(PROJECT_ROOT / "data" / "chat_requests"),
        zeus=ZeusEndpointConfig(
            url=url,
            auth_mode=auth_mode,  # type: ignore[arg-type]
            username=username or None,
            password_env=password_env,
            timeout_s=float(zeus.get("timeout_s") or 60),
        ),
        target=DataTarget(bucket=bucket, scope=scope, collection=collection),
        llm=LlmProviderConfig(
            provider=str(llm.get("provider") or "xai"),
            base_url=base_url,
            model=model,
            api_key_env=api_key_env,
            timeout_s=float(llm.get("timeout_s") or 120),
        ),
        settings=ClientSettings(
            mode=mode,
            durable_sessions=durable,
            ai_process_result=False,
            max_rounds=int(settings_raw.get("max_rounds") or 8),
            ignore_user_tool_path_hints=True,
        ),
    )


def runtime() -> ZeusRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    cfg = _read_app_config()
    _ensure_llm_key(cfg)
    rt = ZeusRuntime(_runtime_config(cfg))
    secrets = rt.services.secrets
    rt.services.zeus = HttpxZeusPort(
        endpoint=rt.config.zeus, secrets=secrets, journal=rt.journal
    )
    rt.services.llm = OpenAICompatibleLlmClient(
        config=rt.config.llm, secrets=secrets, journal=rt.journal
    )
    rt.services.catalog_remote = HttpxCatalogRemote(
        endpoint=rt.config.zeus, secrets=secrets
    )
    _runtime = rt
    return rt


def catalog_flags(doc: dict[str, Any]) -> dict[str, Any]:
    messages = doc.get("messages") if isinstance(doc.get("messages"), list) else []
    content = ""
    if messages and isinstance(messages[0], dict):
        content = str(messages[0].get("content") or "")
    contract = doc.get("contract") if isinstance(doc.get("contract"), dict) else {}
    return {
        "used": bool(messages or doc.get("verbs")),
        "has_scope_brief": "## SCOPE BRIEF" in content,
        "has_mini_schema": "## MINI-SCHEMA" in content,
        "contract_id": str(contract.get("id") or ""),
        "contract_hash": str(contract.get("hash") or doc.get("_hash") or ""),
        "scope": f"{_BUCKET}/{_SCOPE}",
        "mode": _MODE,
    }


async def load_live_chat_request(rt: ZeusRuntime) -> dict[str, Any]:
    """Live stamp for yelp-demo/_default, brief already spliced by Zeus."""
    remote = rt.services.catalog_remote
    if remote is None:
        raise ValueError("catalog remote is not wired")
    doc = await remote.fetch_chat_request(_BUCKET, _SCOPE, _MODE)
    if not isinstance(doc, dict):
        raise ValueError("live chat_request was not a JSON object")
    flags = catalog_flags(doc)
    if not flags["used"] or not flags["has_scope_brief"] or not flags["has_mini_schema"]:
        raise ValueError(
            "live chat_request for yelp-demo/_default has no scope brief or mini-schema"
        )
    return doc


_VERB_NAMES = frozenset(
    {
        "pipeline",
        "find",
        "search",
        "get",
        "describe",
        "project",
        "walk",
        "terminate",
        "return",
    }
)


def _rows_from_turn(result: Any) -> list[dict[str, Any]]:
    debug = getattr(result, "debug", None)
    blobs: list[Any] = []
    hops = getattr(debug, "hops", None) or ()
    if isinstance(hops, (list, tuple)):
        blobs.extend(hops)
    trace = getattr(debug, "public_trace", None)
    if trace:
        blobs.append(trace)
    rows: list[dict[str, Any]] = []

    def looks_like_business(payload: dict[str, Any]) -> bool:
        if payload.get("business_id") or payload.get("doc_key") or payload.get("src_key"):
            return True
        name = str(payload.get("name") or "").strip().lower()
        if not name or name in _VERB_NAMES:
            return False
        if "function" in payload or "arguments" in payload or "tool_calls" in payload:
            return False
        return any(key in payload for key in ("categories", "stars", "city", "address", "rating"))

    def walk(payload: Any, depth: int = 0) -> None:
        if depth > 8 or payload is None:
            return
        if isinstance(payload, str):
            text = payload.strip()
            if text[:1] not in "{[":
                return
            try:
                payload = json.loads(text)
            except ValueError:
                return
        if isinstance(payload, list):
            for item in payload:
                walk(item, depth + 1)
            return
        if not isinstance(payload, dict):
            return
        if looks_like_business(payload):
            rows.append(payload)
        for key in ("items", "results", "rows", "data", "businesses", "nodes", "return"):
            val = payload.get(key)
            if isinstance(val, (dict, list, str)):
                walk(val, depth + 1)
        result_json = payload.get("result_json")
        if isinstance(result_json, (dict, list, str)):
            walk(result_json, depth + 1)

    for blob in blobs:
        walk(blob)
    return rows


async def run_live_search(
    query: str,
    chat_id: str | None = None,
    *,
    ai_process_result: bool = False,
) -> dict[str, Any]:
    message = (query or "").strip()
    if not message:
        raise ValueError("empty query")
    rt = runtime()
    chat_request = await load_live_chat_request(rt)
    flags = catalog_flags(chat_request)
    settings = rt.config.settings.with_updates(ai_process_result=bool(ai_process_result))
    cid = (chat_id or "").strip() or ("yelp_" + uuid.uuid4().hex[:12])
    try:
        result = await rt.agent.run_turn(
            message,
            target=rt.config.target,
            settings=settings,
            chat_request=chat_request,
            chat_id=cid,
            model=rt.config.llm.model,
            enable_sessions=True,
        )
    except ZeusClientError as exc:
        raise RuntimeError(exc.public_message or str(exc)) from exc

    answer = user_facing_answer(result.answer or "")
    err = result.error
    err_text = (getattr(err, "message", None) or "") if err is not None else ""
    status = result.status.value if hasattr(result.status, "value") else str(result.status)
    if result.status == TurnStatus.ERROR:
        raise RuntimeError(err_text or "agent turn failed")

    cards = zeus_data_to_results(_rows_from_turn(result))
    debug = getattr(result, "debug", None)
    trace = getattr(debug, "public_trace", None) if debug is not None else None
    session = getattr(result, "session", None)
    return {
        "chat_id": cid,
        "query": message,
        "answer": answer,
        "structured_answer": None,
        "results": cards,
        "catalog": flags,
        "status": status,
        "session_id": getattr(session, "session_id", None) or "",
        "target": f"{_BUCKET}/{_SCOPE}/_default",
        "mode": _MODE,
        "trace": trace if isinstance(trace, dict) else {},
    }
