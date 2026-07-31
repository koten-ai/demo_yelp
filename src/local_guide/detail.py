"""Business detail + AI review insight helpers."""
from __future__ import annotations

import re
import uuid
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

DEFAULT_REVIEW_LIMIT = 20
MAX_REVIEW_LIMIT = 50
# Graph project often omits review body; N1QL USE KEYS fills text/date.
_REVIEW_N1QL_FIELDS = (
    "text",
    "stars",
    "date",
    "user_id",
    "business_id",
    "review_id",
    "useful",
    "funny",
    "cool",
)
_REVIEW_PROJECT_FIELDS = (
    "text",
    "stars",
    "date",
    "user_id",
    "business_id",
    "review_id",
    "name",
    "useful",
    "funny",
    "cool",
    "doc_key",
    "entity_type",
)


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
        mapped = _review_row_to_ui(row)
        if not mapped.get("text"):
            continue
        out.append(mapped)
        if len(out) >= 10:
            break
    return out


def normalize_yelp_business_id(business_id: str) -> str:
    """Strip optional ``biz:`` prefix used by FTS/doc keys for Yelp academic data."""
    bid = (business_id or "").strip()
    if bid.startswith("biz:"):
        return bid[4:].strip()
    return bid


def _str_field(val: Any) -> str:
    if val is None:
        return ""
    text = str(val).strip()
    return "" if text.lower() in {"none", "null"} else text


def _review_row_to_ui(row: dict[str, Any]) -> dict[str, str]:
    """Map Zeus/N1QL review row → SPA review card shape."""
    text = _str_field(row.get("text") or row.get("description"))
    author = _str_field(row.get("user_id") or row.get("name") or row.get("author"))
    if not author or author == _str_field(row.get("review_id")):
        author = _str_field(row.get("user_id")) or "Reviewer"
    # Avoid dumping raw review_id hashes as the display name when longer.
    if len(author) > 24 and " " not in author:
        author = "Reviewer"
    return {
        "author": author or "Reviewer",
        "stars": _str_field(row.get("stars") if row.get("stars") is not None else row.get("rating")),
        "text": text[:2000],
        "date": _str_field(row.get("date")),
        "review_id": _str_field(row.get("review_id") or row.get("doc_key") or row.get("id")),
    }


def _find_result_keys(body: Any) -> tuple[list[str], list[str]]:
    """Extract (node_ids, doc_keys) from a V2 find response body."""
    if not isinstance(body, dict):
        return [], []
    result = body.get("result") if isinstance(body.get("result"), dict) else body
    if not isinstance(result, dict):
        return [], []
    node_ids: list[str] = []
    for raw in result.get("node_ids") or []:
        s = _str_field(raw)
        if s:
            node_ids.append(s)
    doc_keys: list[str] = []
    for item in result.get("items") or []:
        if not isinstance(item, dict):
            continue
        dk = _str_field(item.get("doc_key") or item.get("source") or item.get("id"))
        if dk and not dk.startswith("n_") and not dk.startswith("file::"):
            doc_keys.append(dk)
        elif dk.startswith("rev:"):
            doc_keys.append(dk)
    # Prefer source-style keys for N1QL USE KEYS.
    seen: set[str] = set()
    uniq_keys: list[str] = []
    for k in doc_keys:
        if k not in seen:
            seen.add(k)
            uniq_keys.append(k)
    return node_ids, uniq_keys


def _project_rows(body: Any) -> list[dict[str, Any]]:
    if not isinstance(body, dict):
        return []
    result = body.get("result") if isinstance(body.get("result"), dict) else body
    if not isinstance(result, dict):
        return []
    rows = result.get("rows") or result.get("items") or []
    return [r for r in rows if isinstance(r, dict) and not r.get("missing")]


def _sample_triple(cfg: dict[str, Any]) -> tuple[str, str, str]:
    sample_name = str(cfg.get("default_sample") or "")
    triple = (cfg.get("samples") or {}).get(sample_name) or {}
    if not triple and isinstance(cfg.get("samples"), dict) and cfg["samples"]:
        triple = next(iter(cfg["samples"].values()))
    bucket = str(triple.get("bucket") or sample_name or "")
    scope = str(triple.get("scope") or "_default")
    collection = str(triple.get("collection") or "_default")
    return bucket, scope, collection


async def fetch_business_reviews(
    business_id: str,
    *,
    limit: int = DEFAULT_REVIEW_LIMIT,
) -> dict[str, Any]:
    """Fetch reviews for a business via Zeus V2 ``find`` (no LLM).

    Uses :func:`zeus_client.run_verb_from_config` → ``find`` with
    ``entity_type=Review`` and ``where.business_id``. Review body text lives on
    source docs, so when Couchbase query config is present we hydrate with
    N1QL ``USE KEYS`` (same helper as fast-tier suggest). Falls back to
    ``project`` on find node ids when N1QL is unavailable.
    """
    from zeus_client import (
        CouchbaseQueryConfig,
        load_config,
        logger,
        resolve_zeus_config,
        run_verb_from_config,
    )
    from zeus_client.zeus.suggest import n1ql_hydrate_keys

    raw_id = (business_id or "").strip()
    bare = normalize_yelp_business_id(raw_id)
    lim = max(1, min(int(limit or DEFAULT_REVIEW_LIMIT), MAX_REVIEW_LIMIT))
    if not bare:
        return {
            "business_id": raw_id,
            "reviews": [],
            "count": 0,
            "source": "none",
            "error": "empty business_id",
            "ai_process_result": False,
        }

    try:
        cfg = await load_config()
    except Exception as e:
        logger.warning("fetch_business_reviews load_config failed: %s", e)
        return {
            "business_id": bare,
            "reviews": [],
            "count": 0,
            "source": "error",
            "error": str(e),
            "ai_process_result": False,
        }

    find_res = await run_verb_from_config(
        "find",
        {
            "entity_type": "Review",
            "where": {"business_id": bare},
            "limit": lim,
        },
        cfg,
        mode_header="analytics",
    )
    if not find_res.ok:
        err = find_res.error or f"find status {find_res.status}"
        logger.warning("fetch_business_reviews find failed: %s", err)
        return {
            "business_id": bare,
            "reviews": [],
            "count": 0,
            "source": "zeus_find",
            "error": err,
            "req_id": find_res.req_id or "",
            "ai_process_result": False,
        }

    node_ids, doc_keys = _find_result_keys(find_res.body)
    rows: list[dict[str, Any]] = []
    source = "zeus_find"
    sources: list[str] = ["zeus_find"]

    zcfg = resolve_zeus_config(cfg)
    zeus_url = str(zcfg.get("url") or "")
    bucket, scope, collection = _sample_triple(cfg)
    cb_raw = cfg.get("couchbase") if isinstance(cfg.get("couchbase"), dict) else None
    cb = CouchbaseQueryConfig.from_mapping(
        cb_raw,
        zeus_url=zeus_url,
        allow_host_default=False,
    )

    if doc_keys and cb is not None:
        try:
            rows = await n1ql_hydrate_keys(
                cb,
                bucket,
                scope,
                collection,
                doc_keys[:lim],
                fields=_REVIEW_N1QL_FIELDS,
            )
            if rows:
                source = "zeus_find+n1ql"
                sources.append("n1ql_hydrate")
        except Exception as e:
            logger.warning("fetch_business_reviews n1ql hydrate failed: %s", e)

    if not rows and node_ids:
        proj = await run_verb_from_config(
            "project",
            {"ids": node_ids[:lim], "fields": list(_REVIEW_PROJECT_FIELDS)},
            cfg,
            mode_header="analytics",
        )
        if proj.ok:
            rows = _project_rows(proj.body)
            if rows:
                source = "zeus_find+project"
                sources.append("zeus_project")

    reviews: list[dict[str, str]] = []
    for row in rows:
        mapped = _review_row_to_ui(row)
        # Keep rows even without text if stars present (sparse graph project).
        if not mapped.get("text") and not mapped.get("stars"):
            continue
        reviews.append(mapped)
        if len(reviews) >= lim:
            break

    return {
        "business_id": bare,
        "reviews": reviews,
        "count": len(reviews),
        "source": source,
        "sources": sources,
        "req_id": find_res.req_id or "",
        "ai_process_result": False,
        "error": None,
    }


def _isolated_detail_chat_id() -> str:
    """Mint a throwaway chat id so detail/insight never share discovery history.

    Discovery multi-turn lives on landing/results/Ask AI ``chat_id`` values.
    Reusing those for ``get_business`` / insight dumps id-lookup tool payloads
    into the durable Zeus session and later synthesis turns (session poison).
    """
    return "detail_" + uuid.uuid4().hex[:12]


async def get_business(business_id: str, chat_id: str | None = None) -> dict:
    """Return a business card, using cache or a short agent fetch.

    ``chat_id`` is accepted for API compatibility but **ignored** for the agent
    path — detail always runs on an isolated session (see session isolation guide).
    """
    from local_guide.business_images import apply_local_images

    # Client may still send the landing/results chat_id; never reuse it here.
    _ = chat_id

    cached = find_cached_business(business_id)
    if cached:
        apply_local_images(cached)
        return {"business": cached, "chat_id": None, "source": "cache"}

    q = (
        f"Get the business with id {business_id} (or matching that identifier). "
        "Return name, categories, stars, review_count, address, city, state, "
        "latitude, longitude, hours, is_open, and price if available."
    )
    # Always fresh chat + Zeus session — do not pass discovery chat_id.
    result = await run_search(q, _isolated_detail_chat_id())
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
    apply_local_images(card)
    return {
        "business": card,
        "chat_id": result.get("chat_id"),
        "trace": result.get("trace"),
        "source": "agent",
        "answer": result.get("answer"),
        "session_id": result.get("session_id"),
        "session_round": result.get("session_round"),
    }


async def run_business_insight(business_id: str, chat_id: str | None = None) -> dict:
    """Agent turn summarizing reviews into good/bad/best-for.

    Isolated from discovery ``chat_id`` / Zeus session (``chat_id`` arg ignored).
    Individual review rows come from :func:`fetch_business_reviews` (direct V2
    ``find``), not from the agent ``zeus_data`` path.
    """
    _ = chat_id

    cached = find_cached_business(business_id)
    label = (cached or {}).get("name") or business_id
    bare = normalize_yelp_business_id(business_id)
    q = (
        f"For business '{label}' (id={bare or business_id}), retrieve related reviews when available "
        "and write an AI review summary with sections **The Good**, **The Bad**, and **Best For** "
        "as bullet lists grounded only in Zeus data. Do not invent reviews."
    )
    result = await run_search(q, _isolated_detail_chat_id())
    if result.get("error"):
        return result

    parsed = parse_insight_answer(result.get("answer"))
    # Prefer direct verb fetch for the review list (0.3.0+ run_verb/find).
    reviews_payload = await fetch_business_reviews(bare or business_id)
    reviews = list(reviews_payload.get("reviews") or [])
    if not reviews:
        reviews = _reviews_from_structured(result.get("structured_response"))
    business = cached
    if not business:
        for c in result.get("results") or []:
            if str(c.get("business_id") or "") == business_id or c.get("name") == label:
                business = c
                break
            if bare and normalize_yelp_business_id(str(c.get("business_id") or "")) == bare:
                business = c
                break

    if isinstance(business, dict):
        from local_guide.business_images import apply_local_images

        apply_local_images(business)

    return {
        "business_id": business_id,
        "business": business,
        "summary": parsed["summary"],
        "the_good": parsed["the_good"],
        "the_bad": parsed["the_bad"],
        "best_for": parsed["best_for"],
        "reviews": reviews,
        "reviews_source": reviews_payload.get("source"),
        "chat_id": result.get("chat_id"),
        "trace": result.get("trace"),
        "answer": result.get("answer"),
        "tool_order": result.get("tool_order"),
        "session_id": result.get("session_id"),
        "session_round": result.get("session_round"),
    }
