"""Business detail + AI review insight helpers."""
from __future__ import annotations

import re
from typing import Any

from local_guide.chat_store import CHATS
from local_guide.search import run_search

_GOOD_BAD = re.compile(
    r"(?is)\*\*\s*(the\s+good|good|pros)\s*\*\*\s*:?\s*(.+?)(?=\*\*\s*(the\s+bad|bad|cons|best)|$)"
)
_THE_BAD = re.compile(
    r"(?is)\*\*\s*(the\s+bad|bad|cons)\s*\*\*\s*:?\s*(.+?)(?=\*\*\s*(best|the\s+good)|$)"
)
_BEST_FOR = re.compile(r"(?is)\*\*\s*(best\s+for)\s*\*\*\s*:?\s*(.+?)(?=\*\*|$)")
_BULLET = re.compile(r"^\s*[-*•]\s+(.+)$", re.MULTILINE)


def find_cached_business(business_id: str) -> dict[str, str] | None:
    """Return a card from in-memory chat last_results matching business_id."""
    bid = (business_id or "").strip()
    if not bid:
        return None
    for chat in CHATS.values():
        for card in chat.get("last_results") or []:
            if not isinstance(card, dict):
                continue
            if str(card.get("business_id") or "").strip() == bid:
                return dict(card)
            if str(card.get("name") or "").strip() == bid:
                return dict(card)
    return None


def _bullets(block: str) -> list[str]:
    items = [m.group(1).strip() for m in _BULLET.finditer(block or "")]
    if items:
        return items[:8]
    parts = re.split(r"[;\n]+", block or "")
    return [p.strip(" -*\t") for p in parts if len(p.strip()) > 3][:8]


def parse_insight_answer(answer: str | None) -> dict[str, Any]:
    text = answer if isinstance(answer, str) else str(answer or "")
    good: list[str] = []
    bad: list[str] = []
    best: list[str] = []
    m = _GOOD_BAD.search(text)
    if m:
        good = _bullets(m.group(2))
    m = _THE_BAD.search(text)
    if m:
        bad = _bullets(m.group(2))
    m = _BEST_FOR.search(text)
    if m:
        best = _bullets(m.group(2))
    return {
        "summary": text.strip()[:1200] if text else "",
        "the_good": good,
        "the_bad": bad,
        "best_for": best,
    }


def _reviews_from_structured(structured_response: dict | None) -> list[dict[str, str]]:
    if not isinstance(structured_response, dict):
        return []
    rows = structured_response.get("zeus_data") or []
    out: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        et = str(row.get("entity_type") or "").lower()
        text = str(row.get("text") or row.get("description") or "").strip()
        if et and et != "review" and not text:
            continue
        if not text:
            continue
        out.append(
            {
                "author": str(row.get("name") or row.get("user_id") or "Reviewer"),
                "stars": str(row.get("stars") or row.get("rating") or ""),
                "text": text[:2000],
                "date": str(row.get("date") or ""),
            }
        )
        if len(out) >= 10:
            break
    return out


async def get_business(business_id: str, chat_id: str | None = None) -> dict:
    """Return a business card, using cache or a short agent fetch."""
    cached = find_cached_business(business_id)
    if cached:
        return {"business": cached, "chat_id": chat_id, "source": "cache"}

    q = (
        f"Get the business with id {business_id} (or matching that identifier). "
        "Return name, categories, stars, review_count, address, city, state, "
        "latitude, longitude, hours, is_open, and price if available."
    )
    result = await run_search(q, chat_id)
    if result.get("error"):
        return result
    card = None
    for c in result.get("results") or []:
        if str(c.get("business_id") or "") == business_id or c.get("name"):
            card = c
            if str(c.get("business_id") or "") == business_id:
                break
    if not card:
        card = {
            "name": business_id,
            "description": "",
            "image": "",
            "business_id": business_id,
        }
    return {
        "business": card,
        "chat_id": result.get("chat_id"),
        "trace": result.get("trace"),
        "source": "agent",
        "answer": result.get("answer"),
    }


async def run_business_insight(business_id: str, chat_id: str | None = None) -> dict:
    """Agent turn summarizing reviews into good/bad/best-for."""
    cached = find_cached_business(business_id)
    label = (cached or {}).get("name") or business_id
    q = (
        f"For business '{label}' (id={business_id}), retrieve related reviews when available "
        "and write an AI review summary with sections **The Good**, **The Bad**, and **Best For** "
        "as bullet lists grounded only in Zeus data. Do not invent reviews."
    )
    result = await run_search(q, chat_id)
    if result.get("error"):
        return result

    parsed = parse_insight_answer(result.get("answer"))
    reviews = _reviews_from_structured(result.get("structured_response"))
    business = cached
    if not business:
        for c in result.get("results") or []:
            if str(c.get("business_id") or "") == business_id or c.get("name") == label:
                business = c
                break

    return {
        "business_id": business_id,
        "business": business,
        "summary": parsed["summary"],
        "the_good": parsed["the_good"],
        "the_bad": parsed["the_bad"],
        "best_for": parsed["best_for"],
        "reviews": reviews,
        "chat_id": result.get("chat_id"),
        "trace": result.get("trace"),
        "answer": result.get("answer"),
        "tool_order": result.get("tool_order"),
        "session_id": result.get("session_id"),
        "session_round": result.get("session_round"),
    }
