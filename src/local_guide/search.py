"""Local business search via the kotenai-zeus-client agent loop."""
from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import replace

import httpx
from zeus_client import TurnStatus, user_facing_answer
from zeus_client.domain.errors import ZeusClientError

from local_guide.answer_parser import parse_markdown_answer, structured_answer_to_results
from local_guide.chat_store import CHATS, chat_lock, persist_chat
from local_guide.chat_trace import inspector_envelope
from local_guide.results_parser import extract_businesses
from local_guide.runtime_factory import get_runtime

logger = logging.getLogger("local_guide.search")

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


def _layer_dict(layer: object) -> dict | None:
    if isinstance(layer, dict):
        return layer
    summary = getattr(layer, "summary", None)
    if isinstance(summary, str):
        return {"summary": summary}
    return None


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
    """Fallback prose when the model returns empty content but cards mapped."""
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


def _new_turns(result) -> list:
    turns = []
    for msg in result.messages:
        if hasattr(msg, "to_openai"):
            turns.append(msg.to_openai())
        elif isinstance(msg, dict):
            turns.append(dict(msg))
    return turns


def _session_bits(result, trace: dict, prior_sid: str, prior_round: int) -> dict:
    returned_sid = str(result.debug.session_id or prior_sid or "")
    session_meta = {
        "session_id": returned_sid,
        "round": result.debug.rounds,
        "contract_status": result.debug.contract_status,
    }
    session_error = str((trace or {}).get("session_error") or "")
    notes = (trace or {}).get("notes") or []
    rehydrate_failed = any(
        isinstance(n, str) and "rehydrate" in n and "failed" in n for n in notes
    )
    turn_conflict = "turn 409" in session_error or (
        session_error.startswith("turn ") and "409" in session_error
    )
    returned_sid = (session_meta.get("session_id") or "").strip()
    session_created = bool((trace or {}).get("session", {}).get("created")) and bool(returned_sid)
    return {
        "session_meta": session_meta,
        "returned_sid": returned_sid,
        "rehydrate_failed": rehydrate_failed,
        "turn_conflict": turn_conflict,
        "session_created": session_created,
        "prior_sid": prior_sid,
        "prior_round": prior_round,
    }


def _finish_answer(query: str, answer: str, result, trace: dict) -> tuple[str, list, dict | None]:
    """Peel the user-facing answer and read cards from hops. Mutates trace notes."""
    layer = _layer_dict(result.layer_a) or {}
    layer_summary = layer.get("summary") if isinstance(layer, dict) else None
    cleaned = user_facing_answer(
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
        notes.append("[WARN] empty model answer; synthesized summary from zeus_data/results")
        trace["notes"] = notes
    return answer, results, structured_answer


def _compose_turn(
    rt,
    result,
    *,
    query: str,
    chat_id: str,
    rewind: bool,
    ai_process_result: bool,
    prior_sid: str,
    prior_round: int,
) -> tuple[dict, dict]:
    """API body plus the fields a stored turn writes. Does not touch CHATS."""
    cfg = rt.config
    zeus_url = (cfg.zeus.url or "").rstrip("/")
    provider_id = cfg.llm.provider or "xai"
    model = cfg.llm.model
    mode = cfg.settings.mode or "analytics"
    envelope = inspector_envelope(
        result,
        rewind=rewind,
        chat_id=chat_id,
        target=cfg.target,
        mode=mode,
        model=model,
        provider=provider_id,
    )
    trace = envelope["trace"]
    raw_answer = result.answer or ""
    bits = _session_bits(result, trace, prior_sid, prior_round)
    answer, results, structured_answer = _finish_answer(query, raw_answer, result, trace)
    session_meta = bits["session_meta"]
    body = {
        "chat_id": chat_id,
        "query": query,
        "answer": answer,
        "structured_answer": structured_answer,
        "structured_response": {
            "answer": answer or "",
            "zeus_data": list(results),
            "warnings": [],
        },
        "results": results,
        "trace": trace,
        "tool_order": envelope["tool_order"],
        "target": envelope["target"],
        "api_version": "v2",
        "mode": mode,
        "base_id": None,
        "model": model,
        "provider": provider_id,
        "zeus_connection": "default",
        "zeus_url": zeus_url,
        "session_id": session_meta.get("session_id") or prior_sid,
        "session_round": session_meta.get("round") or prior_round,
        "contract_status": session_meta.get("contract_status"),
        "ai_process_result": bool(ai_process_result),
        "rewind": envelope["rewind"],
    }
    store = {
        **bits,
        "new_turns": _new_turns(result),
        "raw_answer": raw_answer,
    }
    answer_len = len(answer) if isinstance(answer, str) else len(str(answer or ""))
    logger.info(
        "search complete chat_id=%s results=%d zeus_data=%d structured=%s answer_len=%d",
        chat_id,
        len(results),
        len(results),
        bool(structured_answer),
        answer_len,
    )
    return body, store


def _remember_turn(chat_id: str, query: str, body: dict, store: dict) -> None:
    """Write one normal turn. Rewind never calls this."""
    chat = CHATS[chat_id]
    chat["turns"] = store["new_turns"]
    returned_sid = store["returned_sid"]
    session_meta = store["session_meta"]
    rehydrate_failed = store["rehydrate_failed"]
    turn_conflict = store["turn_conflict"]
    prior_sid = store["prior_sid"]
    prior_round = store["prior_round"]
    if returned_sid:
        chat["zeus_session_id"] = returned_sid
        chat["zeus_round"] = session_meta.get("round") or (
            1 if store["session_created"] else prior_round
        )
        chat["contract_status"] = session_meta.get("contract_status")
        if rehydrate_failed and store["session_created"]:
            logger.info(
                "recovered dead zeus session chat_id=%s prior_sid=%s new_sid=%s",
                chat_id,
                (prior_sid or "")[:16],
                returned_sid[:16],
            )
    elif rehydrate_failed or turn_conflict:
        chat.pop("zeus_session_id", None)
        chat["zeus_round"] = 0
        chat["contract_status"] = session_meta.get("contract_status") or "none"
        logger.warning(
            "dropped dead zeus session chat_id=%s prior_sid=%s rehydrate_failed=%s turn_conflict=%s",
            chat_id,
            (prior_sid or "")[:16],
            rehydrate_failed,
            turn_conflict,
        )
    entry = {
        "question": query,
        "answer": store["raw_answer"],
        "target": body["target"],
        "mode": body["mode"],
        "api_version": body["api_version"],
        "model": body["model"],
        "provider": body["provider"],
        "trace": body["trace"],
        "created": time.time(),
        "session_id": returned_sid or (None if (rehydrate_failed or turn_conflict) else prior_sid),
        "session_round": (
            session_meta.get("round")
            if returned_sid
            else (0 if (rehydrate_failed or turn_conflict) else prior_round)
        ),
        "contract_status": session_meta.get("contract_status"),
    }
    chat.setdefault("traces", []).append(entry)
    chat["last_results"] = body["results"]


async def _open_runtime():
    if not (os.environ.get("LLM_API_KEY") or "").strip():
        raise ValueError("LLM_API_KEY is not set (set it in .env, not config.json)")
    rt = await get_runtime()
    if not (rt.config.zeus.url or "").rstrip("/"):
        raise ValueError("no Zeus URL configured (set ZEUS_URL)")
    return rt


async def _run_turn(rt, *, message: str, chat_id: str, ai_process_result: bool, rewind: bool, prior_messages: tuple):
    cfg = rt.config
    settings = cfg.settings
    if bool(ai_process_result) != bool(settings.ai_process_result):
        settings = replace(settings, ai_process_result=bool(ai_process_result))
    try:
        await rt.catalog.load_for_turn(settings.mode, target=cfg.target)
        result = await rt.agent.run_turn(
            message,
            target=cfg.target,
            settings=settings,
            chat_id=chat_id,
            model=cfg.llm.model,
            enable_sessions=bool(settings.durable_sessions),
            prior_messages=prior_messages,
            rewind=bool(rewind),
        )
    except ZeusClientError as exc:
        raise RuntimeError(exc.public_message or str(exc)) from exc
    if result.status in {TurnStatus.ERROR, TurnStatus.REFUSED}:
        err = getattr(result.error, "message", None) or "agent turn failed"
        raise RuntimeError(str(err))
    return result


async def run_search(
    query: str,
    chat_id: str | None = None,
    *,
    ai_process_result: bool = False,
    rewind: bool = False,
) -> dict:
    """Run one agent turn. Returns success payload or {\"error\": ...}.

    ``ai_process_result`` maps to kotenai-zeus-client ``ClientSettings`` (0.2.1+):
    - ``False`` (default): cheap path for landing / results search cards
    - ``True``: Hub-style insight synthesis for Ask AI multi-turn chat

    A rewind turn never reads or writes the chat store.
    """
    try:
        if rewind:
            return await _rewind_search(
                query,
                chat_id,
                ai_process_result=ai_process_result,
            )
        return await _search_async(
            query,
            chat_id,
            ai_process_result=ai_process_result,
        )
    except RuntimeError as e:
        return {"error": str(e), "rewind": bool(rewind)}
    except ZeusClientError as e:
        return {"error": (e.public_message or str(e)), "rewind": bool(rewind)}
    except httpx.HTTPError as e:
        return {"error": f"network error: {e}", "rewind": bool(rewind)}
    except ValueError as e:
        return {"error": str(e), "rewind": bool(rewind)}


async def _rewind_search(
    query: str,
    chat_id: str | None,
    *,
    ai_process_result: bool = False,
) -> dict:
    """One rewind turn. Does not lock or write CHATS."""
    rt = await _open_runtime()
    message = query.strip()
    chat_id = chat_id or ("yelp_" + uuid.uuid4().hex[:12])
    result = await _run_turn(
        rt,
        message=message,
        chat_id=chat_id,
        ai_process_result=ai_process_result,
        rewind=True,
        prior_messages=(),
    )
    body, _store = _compose_turn(
        rt,
        result,
        query=query,
        chat_id=chat_id,
        rewind=True,
        ai_process_result=ai_process_result,
        prior_sid="",
        prior_round=0,
    )
    return body


async def _search_async(
    query: str,
    chat_id: str | None,
    *,
    ai_process_result: bool = False,
) -> dict:
    """One stored turn. Always writes the chat it runs."""
    rt = await _open_runtime()
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

        prior_messages = tuple(turn for turn in prior_turns if isinstance(turn, dict))
        result = await _run_turn(
            rt,
            message=message,
            chat_id=chat_id,
            ai_process_result=ai_process_result,
            rewind=False,
            prior_messages=prior_messages,
        )
        body, store = _compose_turn(
            rt,
            result,
            query=query,
            chat_id=chat_id,
            rewind=False,
            ai_process_result=ai_process_result,
            prior_sid=prior_sid,
            prior_round=prior_round,
        )
        _remember_turn(chat_id, query, body, store)
        await persist_chat(chat_id)
        return body
