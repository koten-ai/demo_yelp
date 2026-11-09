"""Inspector body for one agent search. Catalog screens do not import this."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_TRUTHY_QUERY = frozenset({"1", "true", "yes", "on"})

# Widget tool axes. v1 is the legacy quartet. v2 includes pipeline.
TOOL_ORDER: dict[str, list[str]] = {
    "v1": ["text_search", "get_by_keys", "find_nodes", "return_result"],
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


def tool_order() -> dict[str, list[str]]:
    return {"v1": list(TOOL_ORDER["v1"]), "v2": list(TOOL_ORDER["v2"])}


def debug_query_enabled(value: object | None) -> bool:
    """True when debug is 1, true, yes, or on."""
    if value is True:
        return True
    if value is False or value is None:
        return False
    return str(value).strip().lower() in _TRUTHY_QUERY


def trace_payload(result: Any, *extra_notes: str) -> dict[str, Any]:
    """Widget trace from public_trace. Hops copy only when that trace has none."""
    debug = result.debug
    raw_public = getattr(debug, "public_trace", None)
    trace: dict[str, Any] = dict(raw_public) if isinstance(raw_public, Mapping) else {}
    notes = tuple(getattr(debug, "notes", None) or ()) + tuple(
        note for note in extra_notes if note
    )
    if notes:
        existing = list(trace.get("notes") or [])
        for note in notes:
            if note not in existing:
                existing.append(note)
        trace["notes"] = existing
    detective = getattr(debug, "detective", None)
    if isinstance(detective, Mapping):
        trace["detective"] = dict(detective)
    preferred = getattr(debug, "preferred_req_id", None)
    if preferred:
        raw_sess = trace.get("session")
        sess = dict(raw_sess) if isinstance(raw_sess, Mapping) else {}
        sess["preferred_req_id"] = preferred
        trace["session"] = sess
    hops = getattr(debug, "hops", None)
    if hops and not trace.get("hops"):
        trace["hops"] = [dict(hop) for hop in hops if isinstance(hop, Mapping)]
    return trace


def inspector_envelope(
    result: Any,
    *,
    rewind: bool,
    chat_id: str,
    target: Any,
    mode: str,
    model: str,
    provider: str,
    extra_notes: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Fields the chat-trace widget reads off an agent search response."""
    return {
        "rewind": bool(rewind),
        "chat_id": chat_id,
        "target": f"{target.bucket}/{target.scope}/{target.collection}",
        "mode": mode,
        "model": model,
        "provider": provider,
        "tool_order": tool_order(),
        "trace": trace_payload(result, *extra_notes),
    }
