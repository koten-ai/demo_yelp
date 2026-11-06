"""Local business search via the kotenai-zeus-client agent loop."""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import asdict, is_dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx
from zeus_client import ClientSettings

from local_guide.answer_parser import parse_markdown_answer, structured_answer_to_results
from local_guide.chat_store import CHATS, chat_lock, persist_chat
from local_guide.output_schema import DEMO_OUTPUT_SCHEMA
from local_guide.results_parser import extract_businesses, zeus_data_to_results
from local_guide.zeus_config import (
    env_text,
    load_config,
    resolve_llm_provider_config,
    resolve_zeus_config,
)

logger = logging.getLogger("local_guide.search")

try:
    from zeus_client import user_facing_answer as _user_facing_answer
except ImportError:  # pragma: no cover - older client pins
    def _user_facing_answer(answer, *, ui_text=None, layer_summary=None):  # type: ignore[misc]
        return answer if isinstance(answer, str) else ("" if answer is None else str(answer))


def normalize_api_version(value: object) -> str:
    text = str(value or "v2").strip().lower()
    return text if text in {"v1", "v2"} else "v2"


def build_tool_order(chats=None):
    try:
        from zeus_client import build_tool_order as client_build
    except ImportError:
        client_build = None
    if client_build is not None:
        return client_build(chats)
    return {
        "v1": [],
        "v2": [
            "describe",
            "explain",
            "get",
            "find",
            "set",
            "order",
            "enrich",
            "project",
            "traverse",
            "pipeline",
            "search",
            "analyze",
            "return",
        ],
    }


async def run_agent(*args, **kwargs):
    from zeus_client import run_agent as client_run_agent

    return await client_run_agent(*args, **kwargs)

LOCAL_PROMPT_PREFIX = (
    "Find local businesses that match these preferences in the yelp-demo knowledge graph. "
    "Use Zeus V2 search, find, get, or pipeline as needed on real data "
    "(Business and related Review entities). "
    "Prefer results with name, categories, stars/rating, review_count, address/city/state, "
    "latitude/longitude, hours/is_open, and price attributes when available. "
    "Do not invent businesses missing from Zeus results. "
    "Summarize why each match fits the user intent.\n\n"
    "Tool discipline (critical):\n"
    "- Always call tools for this turn. Never answer from prior failed turns or invent "
    "\"collection boundary\" outages without a fresh tool error this round.\n"
    "- Prefer ONE pipeline. For location filters (city/state), use find with equality "
    "`where` on MINI-SCHEMA GSI fields (e.g. city:\"Philadelphia\"), then project fields "
    "on @step.ids. Do NOT rely on hybrid/fts alone for city — hybrid where can return "
    "zero while find succeeds.\n"
    "- For free-text category/vibe (grocery, wifi, cafe): FIRST find+project by city "
    "(limit 50–100), then filter/rank in your summary by categories/name. "
    "Avoid FTS/hybrid `narrow_to` on find ids when that path returns empty — "
    "fall back to find→project only.\n"
    "- After FTS/hybrid, project using @step.ids / node_ids returned by that step — "
    "do not batch_get raw source keys like biz:… alone if get returns missing.\n"
    "- pipeline confidence must be a STRING: high|med|low (never an object).\n"
    "- End with return (or terminating pipeline fields) including a real summary.\n\n"
    "User preferences:\n"
)

_EMPTY_ANSWER_MARKERS = {
    "",
    "(model returned no content)",
    "none",
    "null",
}

_POISON_MARKERS = (
    'unknown boundary: "collections"',
    'unknown boundary: \\"collections\\"',
    "No verifiable",
    "collection boundary errors",
)


def _provider_id(provider: dict) -> str:
    label = (provider.get("label") or "").strip().lower()
    if label:
        return label.split()[0]
    host = urlparse(provider.get("base_url") or "").netloc
    return host.split(".")[0] if host else "default"


def _structured_response_payload(structured) -> dict:
    if is_dataclass(structured):
        return asdict(structured)
    return {
        "answer": getattr(structured, "answer", ""),
        "zeus_data": list(getattr(structured, "zeus_data", []) or []),
        "warnings": list(getattr(structured, "warnings", []) or []),
    }


def _resolve_mode(cfg: dict) -> str:
    """ZEUS_MODE from the environment, else config, else analytics."""
    env_mode = env_text("ZEUS_MODE")
    if env_mode:
        return env_mode
    default_mode = str(cfg.get("default_mode") or "").strip()
    if default_mode and default_mode != "ZEUS_MODE":
        return default_mode
    settings = cfg.get("settings") if isinstance(cfg.get("settings"), dict) else {}
    settings_mode = str(settings.get("mode") or "").strip()
    if settings_mode and settings_mode != "ZEUS_MODE":
        return settings_mode
    return "analytics"


def _llm_base_url(provider: dict, llm: dict) -> str:
    base_url = env_text("LLM_BASE_URL")
    if not base_url:
        raw = str(llm.get("base_url") or provider.get("base_url") or "")
        base_url = "" if raw == "LLM_BASE_URL" else raw
    return base_url.rstrip("/")


def _llm_model(provider: dict, llm: dict) -> str:
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


def _message_text(turn: dict) -> str:
    content = turn.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(parts)
    return str(content or "")


def history_looks_poisoned(prior_turns: list | None) -> bool:
    """True when multi-turn context is likely to make the model skip tools.

    Detects long histories and repeated boundary / \"no verifiable\" failure
    narratives from earlier Zeus misconfig (boundary=collections).
    """
    turns = prior_turns or []
    if len(turns) >= 48:
        return True

    boundary_hits = 0
    canned_no_data = 0
    for turn in turns[-30:]:
        if not isinstance(turn, dict):
            continue
        text = _message_text(turn)
        role = turn.get("role") or ""
        if any(m in text for m in _POISON_MARKERS[:2]):
            boundary_hits += 1
        if role == "assistant" and "No verifiable" in text and not turn.get("tool_calls"):
            canned_no_data += 1
        elif role == "assistant" and "collection boundary errors" in text:
            canned_no_data += 1
    return boundary_hits >= 2 or canned_no_data >= 2


def synthesize_answer_from_results(query: str, results: list[dict]) -> str:
    """Fallback prose when the model returns empty content but zeus_data mapped."""
    if not results:
        return ""
    names = [str(r.get("name") or "").strip() for r in results if r.get("name")]
    names = [n for n in names if n][:8]
    if not names:
        return f"Found {len(results)} matching businesses for: {query.strip()}"
    listed = "; ".join(names)
    extra = "" if len(results) <= len(names) else f" (+{len(results) - len(names)} more)"
    return (
        f"Found {len(results)} businesses matching **{query.strip()}**. "
        f"Top matches: {listed}{extra}."
    )


def _answer_is_empty(answer: object) -> bool:
    if answer is None:
        return True
    text = str(answer).strip()
    return text.lower() in _EMPTY_ANSWER_MARKERS


async def run_search(
    query: str,
    chat_id: str | None = None,
    *,
    ai_process_result: bool = False,
) -> dict:
    """Run one agent turn. Returns success payload or {\"error\": ...}.

    ``ai_process_result`` maps to kotenai-zeus-client ``ClientSettings`` (0.2.1+):
    - ``False`` (default): cheap path for landing / results search cards
    - ``True``: Hub-style insight synthesis for Ask AI multi-turn chat
    """
    try:
        return await _search_async(query, chat_id, ai_process_result=ai_process_result)
    except RuntimeError as e:
        return {"error": str(e)}
    except httpx.HTTPError as e:
        return {"error": f"network error: {e}"}
    except ValueError as e:
        return {"error": str(e)}


async def _search_async(
    query: str,
    chat_id: str | None,
    *,
    ai_process_result: bool = False,
) -> dict:
    cfg = await load_config()
    zcfg = resolve_zeus_config(cfg)
    zeus_url = (env_text("ZEUS_URL") or str(zcfg.get("url") or "")).rstrip("/")
    zeus_connection = zcfg.get("name") or "default"
    if not zeus_url:
        raise ValueError("no Zeus URL configured (set ZEUS_URL)")

    provider = resolve_llm_provider_config(cfg) or {}
    llm = cfg.get("llm") if isinstance(cfg.get("llm"), dict) else {}
    base_url = _llm_base_url(provider, llm)
    # Never pass llm_provider.api_key. The value is LLM_API_KEY from the environment.
    api_key = env_text("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY is not set (set it in .env, not config.json)")
    provider_id = _provider_id(
        {
            "label": provider.get("label") or llm.get("label") or llm.get("provider"),
            "base_url": base_url,
        }
    )
    model = _llm_model(provider, llm)

    api_version = normalize_api_version(cfg.get("default_api_version", "v2"))
    # Product default is analytics (base-6.1); older configs may still say "auto"/"open".
    mode = _resolve_mode(cfg)
    base_id = (cfg.get("default_base_id") or "").strip() or None
    raw_base_dirs = cfg.get("base_catalog_dirs") or []
    base_catalog_dirs: list[Path] | None = None
    if isinstance(raw_base_dirs, (list, tuple)) and raw_base_dirs:
        base_catalog_dirs = [Path(str(p)) for p in raw_base_dirs if str(p).strip()]
        if not base_catalog_dirs:
            base_catalog_dirs = None
    sample = cfg.get("default_sample", "yelp-demo")
    samples = cfg.get("samples") if isinstance(cfg.get("samples"), dict) else {}
    triple = samples.get(sample) if isinstance(samples.get(sample), dict) else {}
    if not triple and isinstance(cfg.get("target"), dict):
        triple = cfg["target"]
    bucket = triple.get("bucket", sample)
    scope = triple.get("scope", "_default")
    collection = triple.get("collection", "_default")

    message = query.strip()
    chat_id = chat_id or ("yelp_" + uuid.uuid4().hex[:12])

    lock = await chat_lock(chat_id)
    async with lock:
        if chat_id not in CHATS:
            CHATS[chat_id] = {
                "title": query[:48],
                "created": time.time(),
                "turns": [],
                "traces": [],
                "last_results": [],
            }
        prior_turns = list(CHATS[chat_id]["turns"] or [])
        prior_sid = CHATS[chat_id].get("zeus_session_id", "") or ""
        prior_round = int(CHATS[chat_id].get("zeus_round", 0) or 0)

        if history_looks_poisoned(prior_turns):
            logger.warning(
                "resetting poisoned chat history chat_id=%s turns=%d prior_sid=%s",
                chat_id,
                len(prior_turns),
                (prior_sid or "")[:16],
            )
            prior_turns = []
            prior_sid = ""
            prior_round = 0
            CHATS[chat_id]["turns"] = []
            CHATS[chat_id].pop("zeus_session_id", None)
            CHATS[chat_id]["zeus_round"] = 0

        settings = ClientSettings(ai_process_result=bool(ai_process_result))
        answer, trace, new_turns, session_meta, structured = await run_agent(
            zeus_url,
            zcfg,
            base_url,
            api_key,
            model,
            api_version,
            mode,
            bucket,
            scope,
            collection,
            message,
            prior_turns,
            optimized=True,
            provider_id=provider_id,
            conv_id=chat_id,
            zeus_session_id=prior_sid,
            zeus_round=prior_round,
            structured=True,
            output_schema=DEMO_OUTPUT_SCHEMA,
            settings=settings,
            base_id=base_id,
            base_catalog_dirs=base_catalog_dirs,
            api_key_env="LLM_API_KEY",
        )

        CHATS[chat_id]["turns"] = new_turns
        session_error = str((trace or {}).get("session_error") or "")
        notes = (trace or {}).get("notes") or []
        rehydrate_failed = any(
            isinstance(n, str) and "rehydrate" in n and "failed" in n for n in notes
        )
        turn_conflict = "turn 409" in session_error or (
            session_error.startswith("turn ") and "409" in session_error
        )
        # Client now recreates a durable session same-turn when rehydrate fails.
        # Prefer the sid returned from this turn; only drop when nothing usable
        # came back (create also failed, or turn conflict without a new sid).
        returned_sid = (session_meta.get("session_id") or "").strip()
        session_created = bool((trace or {}).get("session", {}).get("created")) and bool(
            returned_sid
        )
        if returned_sid:
            CHATS[chat_id]["zeus_session_id"] = returned_sid
            CHATS[chat_id]["zeus_round"] = session_meta.get("round") or (
                1 if session_created else prior_round
            )
            CHATS[chat_id]["contract_status"] = session_meta.get("contract_status")
            if rehydrate_failed and session_created:
                logger.info(
                    "recovered dead zeus session chat_id=%s prior_sid=%s new_sid=%s",
                    chat_id,
                    (prior_sid or "")[:16],
                    returned_sid[:16],
                )
        elif rehydrate_failed or turn_conflict:
            CHATS[chat_id].pop("zeus_session_id", None)
            CHATS[chat_id]["zeus_round"] = 0
            CHATS[chat_id]["contract_status"] = session_meta.get("contract_status") or "none"
            logger.warning(
                "dropped dead zeus session chat_id=%s prior_sid=%s rehydrate_failed=%s turn_conflict=%s",
                chat_id,
                (prior_sid or "")[:16],
                rehydrate_failed,
                turn_conflict,
            )

        target = f"{bucket}/{scope}/{collection}"
        entry = {
            "question": query,
            "answer": answer,
            "target": target,
            "mode": mode,
            "api_version": api_version,
            "model": model,
            "provider": provider_id,
            "trace": trace,
            "created": time.time(),
            "session_id": returned_sid or (None if (rehydrate_failed or turn_conflict) else prior_sid),
            "session_round": (
                session_meta.get("round")
                if returned_sid
                else (0 if (rehydrate_failed or turn_conflict) else prior_round)
            ),
            "contract_status": session_meta.get("contract_status"),
        }
        CHATS[chat_id].setdefault("traces", []).append(entry)

        results = zeus_data_to_results(structured.zeus_data)
        if not results:
            results = extract_businesses(trace)

        # Ask AI / ai_process insight sometimes returns a fenced Layer A dump
        # (summary + policy_action + wish_i_knew …). Prefer ui_text / peeled summary.
        layer = getattr(structured, "layer_a", None) or {}
        layer_summary = layer.get("summary") if isinstance(layer, dict) else None
        cleaned = _user_facing_answer(
            answer if isinstance(answer, str) else str(answer or ""),
            ui_text=getattr(structured, "ui_text", None),
            layer_summary=layer_summary if isinstance(layer_summary, str) else None,
        )
        if cleaned and cleaned != (answer or ""):
            answer = cleaned
            try:
                structured.answer = answer  # type: ignore[attr-defined]
            except Exception:
                pass
            if isinstance(trace, dict):
                notes = list(trace.get("notes") or [])
                notes.append("[WARN] peeled Layer A envelope from Ask AI answer")
                trace["notes"] = notes

        structured_answer = parse_markdown_answer(answer)
        if not results and structured_answer:
            results = structured_answer_to_results(structured_answer)

        if _answer_is_empty(answer) and results:
            answer = synthesize_answer_from_results(query, results)
            try:
                structured.answer = answer  # type: ignore[attr-defined]
            except Exception:
                pass
            if isinstance(trace, dict):
                notes = list(trace.get("notes") or [])
                notes.append(
                    "[WARN] empty model answer; synthesized summary from zeus_data/results"
                )
                trace["notes"] = notes

        CHATS[chat_id]["last_results"] = results
        await persist_chat(chat_id)

    answer_len = len(answer) if isinstance(answer, str) else len(str(answer or ""))
    logger.info(
        "search complete chat_id=%s results=%d zeus_data=%d structured=%s answer_len=%d",
        chat_id,
        len(results),
        len(structured.zeus_data),
        bool(structured_answer),
        answer_len,
    )

    return {
        "chat_id": chat_id,
        "query": query,
        "answer": answer,
        "structured_answer": structured_answer,
        "structured_response": _structured_response_payload(structured),
        "results": results,
        "trace": trace,
        "tool_order": build_tool_order(CHATS),
        "target": target,
        "api_version": api_version,
        "mode": mode,
        "base_id": base_id,
        "model": model,
        "provider": provider_id,
        "zeus_connection": zeus_connection,
        "zeus_url": zeus_url,
        "session_id": session_meta.get("session_id") or prior_sid,
        "session_round": session_meta.get("round") or prior_round,
        "contract_status": session_meta.get("contract_status"),
        "ai_process_result": bool(ai_process_result),
    }
