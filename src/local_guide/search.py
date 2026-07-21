"""Local business search via the kotenai-zeus-client agent loop."""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from urllib.parse import urlparse

import httpx
from zeus_client import (
    StructuredAgentResponse,
    build_tool_order,
    load_config,
    logger,
    normalize_api_version,
    resolve_llm_provider_config,
    resolve_zeus_config,
    run_agent,
)

from local_guide.answer_parser import parse_markdown_answer, structured_answer_to_results
from local_guide.chat_store import CHATS, chat_lock, persist_chat
from local_guide.output_schema import DEMO_OUTPUT_SCHEMA
from local_guide.results_parser import extract_businesses, zeus_data_to_results

LOCAL_PROMPT_PREFIX = (
    "Find local businesses that match these preferences in the yelp-demo knowledge graph. "
    "Use Zeus V2 search, find, get, or pipeline as needed on real data "
    "(Business and related Review entities). "
    "Prefer results with name, categories, stars/rating, review_count, address/city/state, "
    "latitude/longitude, hours/is_open, and price attributes when available. "
    "Do not invent businesses missing from Zeus results. "
    "Summarize why each match fits the user intent.\n\n"
    "User preferences:\n"
)


def _provider_id(provider: dict) -> str:
    label = (provider.get("label") or "").strip().lower()
    if label:
        return label.split()[0]
    host = urlparse(provider.get("base_url") or "").netloc
    return host.split(".")[0] if host else "default"


def _structured_response_payload(structured: StructuredAgentResponse) -> dict:
    return asdict(structured)


async def run_search(query: str, chat_id: str | None = None) -> dict:
    """Run one agent turn. Returns success payload or {\"error\": ...}."""
    try:
        return await _search_async(query, chat_id)
    except RuntimeError as e:
        return {"error": str(e)}
    except httpx.HTTPError as e:
        return {"error": f"network error: {e}"}
    except ValueError as e:
        return {"error": str(e)}


async def _search_async(query: str, chat_id: str | None) -> dict:
    cfg = await load_config()
    zcfg = resolve_zeus_config(cfg)
    zeus_url = (zcfg.get("url") or "").rstrip("/")
    zeus_connection = zcfg.get("name") or "default"
    if not zeus_url:
        raise ValueError("no Zeus URL configured (edit config.json)")

    provider = resolve_llm_provider_config(cfg)
    base_url = (provider.get("base_url") or "").rstrip("/")
    api_key = provider.get("api_key") or ""
    provider_id = _provider_id(provider)
    if not api_key:
        raise ValueError("llm_provider has no api_key set (edit config.json)")
    model = (provider.get("models") or ["gpt-4o"])[0]

    api_version = normalize_api_version(cfg.get("default_api_version", "v2"))
    mode = cfg.get("default_mode", "open")
    sample = cfg.get("default_sample", "yelp-demo")
    triple = cfg.get("samples", {}).get(sample, {})
    bucket = triple.get("bucket", sample)
    scope = triple.get("scope", "_default")
    collection = triple.get("collection", "_default")

    message = LOCAL_PROMPT_PREFIX + query.strip()
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
        prior_turns = CHATS[chat_id]["turns"]
        prior_sid = CHATS[chat_id].get("zeus_session_id", "") or ""
        prior_round = int(CHATS[chat_id].get("zeus_round", 0) or 0)

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
        )

        CHATS[chat_id]["turns"] = new_turns
        if session_meta.get("session_id"):
            CHATS[chat_id]["zeus_session_id"] = session_meta["session_id"]
            CHATS[chat_id]["zeus_round"] = session_meta.get("round") or prior_round
            CHATS[chat_id]["contract_status"] = session_meta.get("contract_status")

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
            "session_id": session_meta.get("session_id") or prior_sid,
            "session_round": session_meta.get("round") or prior_round,
            "contract_status": session_meta.get("contract_status"),
        }
        CHATS[chat_id].setdefault("traces", []).append(entry)

        results = zeus_data_to_results(structured.zeus_data)
        if not results:
            results = extract_businesses(trace)
        structured_answer = parse_markdown_answer(answer)
        if not results and structured_answer:
            results = structured_answer_to_results(structured_answer)

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
        "model": model,
        "provider": provider_id,
        "zeus_connection": zeus_connection,
        "zeus_url": zeus_url,
        "session_id": session_meta.get("session_id") or prior_sid,
        "session_round": session_meta.get("round") or prior_round,
        "contract_status": session_meta.get("contract_status"),
    }
