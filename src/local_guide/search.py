"""Local business search via the kotenai-zeus-client agent loop."""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import replace

import httpx
from zeus_client import TurnStatus
from zeus_client.domain.errors import ZeusClientError

from local_guide.answer_parser import parse_markdown_answer, structured_answer_to_results
from local_guide.chat_store import CHATS, chat_lock, persist_chat
from local_guide.results_parser import extract_businesses
from local_guide.zeus_config import client_symbol, env_text, get_runtime

logger = logging.getLogger("local_guide.search")

_user_facing_answer = client_symbol("user_facing_answer")
if _user_facing_answer is None:
    def _user_facing_answer(answer, *, ui_text=None, layer_summary=None):  # type: ignore[misc]
        return answer if isinstance(answer, str) else ("" if answer is None else str(answer))


def _layer_dict(layer: object) -> dict | None:
    if isinstance(layer, dict):
        return layer
    summary = getattr(layer, "summary", None)
    if isinstance(summary, str):
        return {"summary": summary}
    return None


# App catalog used when this zeus_client build does not export build_tool_order.
_APP_TOOL_ORDER = {
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


def build_tool_order(chats=None):
    client_build = client_symbol("build_tool_order")
    if client_build is None:
        return _APP_TOOL_ORDER
    return client_build(chats)


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
    """One agent turn. Target, mode, and model come from the runtime."""
    if not env_text("LLM_API_KEY"):
        raise ValueError("LLM_API_KEY is not set (set it in .env, not config.json)")

    rt = await get_runtime()
    zeus_url = str(rt.config.zeus.url or "").rstrip("/")
    if not zeus_url:
        raise ValueError("no Zeus URL configured (set ZEUS_URL)")

    settings = rt.config.settings
    if bool(ai_process_result) != bool(settings.ai_process_result):
        settings = replace(settings, ai_process_result=bool(ai_process_result))
    mode = str(settings.mode or "analytics")
    model = str(rt.config.llm.model or "")
    provider_id = str(getattr(rt.config.llm, "provider", "") or "xai")
    target_obj = rt.config.target
    target = f"{target_obj.bucket}/{target_obj.scope}/{target_obj.collection}"

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
        if history_looks_poisoned(prior_turns):
            logger.warning(
                "resetting poisoned chat history chat_id=%s turns=%d",
                chat_id,
                len(prior_turns),
            )
            prior_turns = []
            CHATS[chat_id]["turns"] = []

        prior_messages = tuple(turn for turn in prior_turns if isinstance(turn, dict))
        try:
            # chat_request and base_id stay omitted so the live catalog is loaded.
            await rt.catalog.load_for_turn(settings.mode, target=rt.config.target)
            result = await rt.agent.run_turn(
                message,
                target=rt.config.target,
                settings=settings,
                chat_id=chat_id,
                model=model,
                enable_sessions=bool(settings.durable_sessions),
                prior_messages=prior_messages,
            )
        except ZeusClientError as exc:
            raise RuntimeError(exc.public_message or str(exc)) from exc
        if result.status in {TurnStatus.ERROR, TurnStatus.REFUSED}:
            err = getattr(result.error, "message", None) or "agent turn failed"
            raise RuntimeError(str(err))

        trace = result.debug.to_dict()
        trace["tool_calls"] = [dict(hop) for hop in result.debug.hops]
        new_turns = []
        for msg in result.messages:
            if hasattr(msg, "to_openai"):
                new_turns.append(msg.to_openai())
            elif isinstance(msg, dict):
                new_turns.append(dict(msg))

        answer = result.answer or ""
        layer = _layer_dict(getattr(result, "layer_a", None))
        layer_summary = layer.get("summary") if isinstance(layer, dict) else None
        cleaned = _user_facing_answer(
            answer if isinstance(answer, str) else str(answer or ""),
            ui_text=None,
            layer_summary=layer_summary if isinstance(layer_summary, str) else None,
        )
        if cleaned and cleaned != (answer or ""):
            answer = cleaned
            notes = list(trace.get("notes") or [])
            notes.append("[WARN] peeled Layer A envelope from Ask AI answer")
            trace["notes"] = notes

        results = extract_businesses(trace)
        structured_answer = parse_markdown_answer(answer)
        if not results and structured_answer:
            results = structured_answer_to_results(structured_answer)

        if _answer_is_empty(answer) and results:
            answer = synthesize_answer_from_results(query, results)
            notes = list(trace.get("notes") or [])
            notes.append("[WARN] empty model answer; synthesized summary from results")
            trace["notes"] = notes

        session_id = str(getattr(result.debug, "session_id", "") or "")
        session_round = result.debug.rounds
        contract_status = result.debug.contract_status
        CHATS[chat_id]["turns"] = new_turns
        CHATS[chat_id]["last_results"] = results
        CHATS[chat_id].setdefault("traces", []).append(
            {
                "question": query,
                "answer": answer,
                "target": target,
                "mode": mode,
                "api_version": "v2",
                "model": model,
                "provider": provider_id,
                "trace": trace,
                "created": time.time(),
                "session_id": session_id or None,
                "session_round": session_round,
                "contract_status": contract_status,
            }
        )
        await persist_chat(chat_id)

    logger.info(
        "search complete chat_id=%s results=%d structured=%s answer_len=%d",
        chat_id,
        len(results),
        bool(structured_answer),
        len(answer) if isinstance(answer, str) else len(str(answer or "")),
    )

    return {
        "chat_id": chat_id,
        "query": query,
        "answer": answer,
        "structured_answer": structured_answer,
        "structured_response": {"answer": answer, "zeus_data": [], "warnings": []},
        "results": results,
        "trace": trace,
        "tool_order": build_tool_order(CHATS),
        "target": target,
        "api_version": "v2",
        "mode": mode,
        "model": model,
        "provider": provider_id,
        "zeus_connection": "default",
        "zeus_url": zeus_url,
        "session_id": session_id,
        "session_round": session_round,
        "contract_status": contract_status,
        "ai_process_result": bool(ai_process_result),
    }
