"""Fast-tier typeahead via kotenai-zeus-client run_fast_suggest (no LLM)."""
from __future__ import annotations

from typing import Any

from zeus_client import SuggestOptions, load_config, logger, run_fast_suggest_from_config

DEFAULT_LIMIT = 8
MIN_QUERY_LEN = 2
MAX_LIMIT = 20


def _str(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, float):
        # Prefer compact rating display (4.5 not 4.500000)
        if val == int(val):
            return str(int(val))
        return f"{val:g}"
    text = str(val).strip()
    return "" if text.lower() in {"none", "null"} else text


def hit_to_card(hit: dict[str, Any]) -> dict[str, str]:
    """Map library SuggestHit dict → demo BusinessCard-shaped row."""
    biz_id = _str(hit.get("id") or hit.get("business_id") or hit.get("doc_key"))
    name = _str(hit.get("name")) or biz_id
    city = _str(hit.get("city"))
    state = _str(hit.get("state"))
    address = _str(hit.get("address"))
    categories = hit.get("categories")
    if isinstance(categories, list):
        categories = ", ".join(_str(c) for c in categories if _str(c))
    else:
        categories = _str(categories)
    stars = hit.get("stars")
    if stars is None:
        stars = hit.get("rating")
    review_count = hit.get("review_count")
    subtitle = _str(hit.get("subtitle"))
    location = ", ".join(p for p in (city, state) if p)
    if not location and address:
        location = address
    description = subtitle or location or categories
    return {
        "name": name,
        "description": description,
        "image": "",
        "business_id": biz_id,
        "rating": _str(stars),
        "review_count": _str(review_count),
        "categories": categories,
        "price": "",
        "is_open": "",
        "hours_today": "",
        "location": location,
        "address": address,
        "city": city,
        "state": state,
        "latitude": _str(hit.get("latitude")),
        "longitude": _str(hit.get("longitude")),
        "url": "",
        # Extra typeahead fields (ignored by card normalizer when unused).
        "subtitle": subtitle,
        "source": _str(hit.get("source")),
    }


def empty_suggest(
    query: str = "",
    *,
    source: str = "none",
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "query": query or "",
        "results": [],
        "count": 0,
        "source": source,
        "sources": [],
        "fast_tier": True,
        "ai_process_result": False,
        "error": error,
    }


async def run_suggest(query: str, *, limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
    """No-LLM suggest for the home SearchBar dropdown.

    Soft-fails to empty results so the combobox stays quiet on Zeus/N1QL blips.
    """
    q = (query or "").strip()
    lim = max(1, min(int(limit or DEFAULT_LIMIT), MAX_LIMIT))
    if len(q) < MIN_QUERY_LEN:
        return empty_suggest(q, source="none")

    try:
        cfg = await load_config()
        result = await run_fast_suggest_from_config(
            q,
            cfg,
            options=SuggestOptions(
                limit=lim,
                min_query_len=MIN_QUERY_LEN,
                fts_timeout_ms=2000,
                entity_type="Business",
                use_fts=True,
                use_find_name=True,
                use_find_city=True,
                use_n1ql_hydrate=True,
                mode_header="analytics",
            ),
        )
        payload = result.to_dict()
        cleaned: list[dict[str, str]] = []
        for h in payload.get("results") or []:
            if not isinstance(h, dict):
                continue
            card = hit_to_card(h)
            name = card.get("name") or ""
            bid = card.get("business_id") or ""
            if not name:
                continue
            # Drop FTS key-only placeholders (name == biz:…).
            if name == bid and bid.startswith("biz:"):
                continue
            cleaned.append(card)
        return {
            "query": payload.get("query") or q,
            "results": cleaned,
            "count": len(cleaned),
            "source": payload.get("source") or ("empty" if not cleaned else "unknown"),
            "sources": list(payload.get("sources") or []),
            "target": payload.get("target") or "",
            "zeus_url": payload.get("zeus_url") or "",
            "fts_req_id": payload.get("fts_req_id") or "",
            "fast_tier": True,
            "ai_process_result": False,
            # Soft surface: never force a 5xx from library error string alone.
            "error": payload.get("error") or None,
        }
    except Exception as e:
        logger.warning("run_suggest failed: %s", e)
        return empty_suggest(q, source="error", error=str(e))
