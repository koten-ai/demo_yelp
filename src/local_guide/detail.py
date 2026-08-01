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
# Yelp academic User source docs (keys: user:<user_id>).
_USER_N1QL_FIELDS = (
    "user_id",
    "name",
    "review_count",
    "average_stars",
    "yelping_since",
    "useful",
    "funny",
    "cool",
)
_USER_PROJECT_FIELDS = (
    "user_id",
    "name",
    "review_count",
    "average_stars",
    "yelping_since",
    "doc_key",
    "entity_type",
)
# Business source docs hold card fields; graph project is a thinner fallback.
_BUSINESS_N1QL_FIELDS = (
    "name",
    "city",
    "state",
    "stars",
    "review_count",
    "categories",
    "address",
    "latitude",
    "longitude",
    "business_id",
    "hours",
    "is_open",
    "attributes",
    "postal_code",
)
_BUSINESS_PROJECT_FIELDS = (
    "name",
    "city",
    "state",
    "stars",
    "review_count",
    "categories",
    "address",
    "latitude",
    "longitude",
    "business_id",
    "hours",
    "is_open",
    "doc_key",
    "entity_type",
)


def _business_ids_equal(a: str, b: str) -> bool:
    """Match bare Yelp ids, biz: keys, and exact string equality."""
    sa = (a or "").strip()
    sb = (b or "").strip()
    if not sa or not sb:
        return False
    if sa == sb:
        return True
    return normalize_yelp_business_id(sa) == normalize_yelp_business_id(sb)


def find_cached_business(business_id: str) -> dict[str, str] | None:
    """Return a card from in-memory chat last_results matching business_id."""
    bid = (business_id or "").strip()
    if not bid:
        return None
    for chat in CHATS.values():
        for card in chat.get("last_results") or []:
            if not isinstance(card, dict):
                continue
            if _business_ids_equal(str(card.get("business_id") or ""), bid):
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


def normalize_yelp_user_id(user_id: str) -> str:
    """Strip optional ``user:`` prefix from Yelp academic user keys / ids."""
    uid = (user_id or "").strip()
    if uid.startswith("user:"):
        return uid[5:].strip()
    return uid


def yelp_user_doc_key(user_id: str) -> str:
    """Couchbase doc key for a Yelp user (``user:<bare_id>``)."""
    bare = normalize_yelp_user_id(user_id)
    return f"user:{bare}" if bare else ""


def _str_field(val: Any) -> str:
    if val is None:
        return ""
    text = str(val).strip()
    return "" if text.lower() in {"none", "null"} else text


def _looks_like_yelp_opaque_id(value: str) -> bool:
    """True for bare Yelp academic ids (∼22-char base64url), not human names."""
    s = (value or "").strip()
    if len(s) < 16 or " " in s:
        return False
    return all(c.isalnum() or c in "-_" for c in s)


def _user_lookup_keys(user_ids: list[str]) -> list[str]:
    """Unique ``user:<id>`` keys preserving first-seen order."""
    seen: set[str] = set()
    keys: list[str] = []
    for raw in user_ids:
        key = yelp_user_doc_key(_str_field(raw))
        if not key or key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys


def _index_users_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index hydrated User rows by bare ``user_id`` (and doc_key bare form)."""
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        uid = normalize_yelp_user_id(
            _str_field(row.get("user_id") or row.get("doc_key") or row.get("id"))
        )
        if not uid:
            continue
        out[uid] = row
    return out


def _review_row_to_ui(
    row: dict[str, Any],
    user: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Map Zeus/N1QL review row (+ optional User doc) → SPA review card shape."""
    text = _str_field(row.get("text") or row.get("description"))
    bare_uid = normalize_yelp_user_id(_str_field(row.get("user_id")))
    user_row = user if isinstance(user, dict) else None
    if user_row is None and bare_uid and isinstance(row.get("_user"), dict):
        user_row = row["_user"]  # type: ignore[assignment]

    display_name = ""
    user_review_count = ""
    user_average_stars = ""
    yelping_since = ""
    if user_row:
        display_name = _str_field(user_row.get("name") or user_row.get("user_name"))
        if user_row.get("review_count") is not None:
            user_review_count = _str_field(user_row.get("review_count"))
        if user_row.get("average_stars") is not None:
            user_average_stars = _str_field(user_row.get("average_stars"))
        yelping_since = _str_field(user_row.get("yelping_since"))

    author = display_name or _str_field(row.get("name") or row.get("author"))
    if not author or author == _str_field(row.get("review_id")):
        author = display_name or bare_uid or "Reviewer"
    # Opaque Yelp ids are not display names when User join missed.
    if not display_name and _looks_like_yelp_opaque_id(author):
        author = "Reviewer"
    return {
        "author": author or "Reviewer",
        "stars": _str_field(row.get("stars") if row.get("stars") is not None else row.get("rating")),
        "text": text[:2000],
        "date": _str_field(row.get("date")),
        "review_id": _str_field(row.get("review_id") or row.get("doc_key") or row.get("id")),
        "user_id": bare_uid,
        "user_review_count": user_review_count,
        "user_average_stars": user_average_stars,
        "yelping_since": yelping_since,
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

    # Batch-join User docs via entity_fk user_id (N1QL USE KEYS user:<id>).
    # Soft-fail: reviews still render with generic author if users missing.
    users_by_id: dict[str, dict[str, Any]] = {}
    user_keys = _user_lookup_keys(
        [_str_field(r.get("user_id")) for r in rows if isinstance(r, dict)]
    )
    if user_keys and cb is not None:
        try:
            user_rows = await n1ql_hydrate_keys(
                cb,
                bucket,
                scope,
                collection,
                user_keys[:lim],
                fields=_USER_N1QL_FIELDS,
            )
            users_by_id = _index_users_by_id(user_rows)
            if users_by_id:
                sources.append("n1ql_user_hydrate")
                if "+users" not in source:
                    source = f"{source}+users"
        except Exception as e:
            logger.warning("fetch_business_reviews user n1ql hydrate failed: %s", e)
    if user_keys and not users_by_id and cb is None:
        # Pure-Zeus fallback: find each unique User (capped) then project.
        # Prefer N1QL when available — this path is slower and best-effort.
        try:
            found_user_node_ids: list[str] = []
            for uk in user_keys[: min(10, lim)]:
                bare_uid = normalize_yelp_user_id(uk)
                if not bare_uid:
                    continue
                ufind = await run_verb_from_config(
                    "find",
                    {
                        "entity_type": "User",
                        "where": {"user_id": bare_uid},
                        "limit": 1,
                    },
                    cfg,
                    mode_header="analytics",
                )
                if not ufind.ok:
                    continue
                u_nids, _ = _find_result_keys(ufind.body)
                found_user_node_ids.extend(u_nids[:1])
            if found_user_node_ids:
                uproj = await run_verb_from_config(
                    "project",
                    {
                        "ids": found_user_node_ids[:lim],
                        "fields": list(_USER_PROJECT_FIELDS),
                    },
                    cfg,
                    mode_header="analytics",
                )
                if uproj.ok:
                    users_by_id = _index_users_by_id(_project_rows(uproj.body))
                    if users_by_id:
                        sources.append("zeus_user_find_project")
                        if "+users" not in source:
                            source = f"{source}+users"
        except Exception as e:
            logger.warning("fetch_business_reviews user find/project failed: %s", e)

    reviews: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        uid = normalize_yelp_user_id(_str_field(row.get("user_id")))
        mapped = _review_row_to_ui(row, user=users_by_id.get(uid))
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
    Reusing those for insight dumps id-lookup tool payloads into the durable
    Zeus session and later synthesis turns (session poison). Business card
    seed uses direct V2 ``find`` (no chat).
    """
    return "detail_" + uuid.uuid4().hex[:12]


def _biz_doc_key(raw_id: str, bare: str) -> str:
    """Yelp academic source keys are ``biz:<id>``."""
    rid = (raw_id or "").strip()
    if rid.startswith("biz:"):
        return rid
    if bare:
        return f"biz:{bare}"
    return rid


def _card_from_find_item(item: dict[str, Any], *, raw_id: str, bare: str) -> dict[str, str] | None:
    """Minimal card from find ``items[]`` when hydrate/project is empty."""
    name = _str_field(item.get("name") or item.get("title"))
    if not name:
        return None
    doc_key = _str_field(item.get("doc_key") or item.get("source") or item.get("id"))
    bid = doc_key if doc_key.startswith("biz:") else (_biz_doc_key(raw_id, bare) or bare or raw_id)
    return {
        "name": name,
        "description": "",
        "image": "",
        "business_id": bid or bare or raw_id,
    }


def _row_to_business_card(row: dict[str, Any], *, fallback_id: str = "") -> dict[str, str] | None:
    """Map Zeus/N1QL business row → SPA BusinessCard shape."""
    from local_guide.results_parser import _normalize_row

    card = _normalize_row(row)
    if card:
        if not card.get("business_id") and fallback_id:
            card["business_id"] = fallback_id
        return card
    name = _str_field(row.get("name") or row.get("title"))
    if not name:
        return None
    bid = _str_field(row.get("business_id") or row.get("doc_key") or row.get("id") or fallback_id)
    return {
        "name": name,
        "description": "",
        "image": "",
        "business_id": bid or fallback_id,
    }


async def fetch_business_via_find(business_id: str) -> dict[str, Any]:
    """Fetch one business card via Zeus V2 ``find`` (no LLM).

    ``find`` entity_type=Business where business_id=<bare> (strip optional
    ``biz:``), then hydrate source fields with N1QL ``USE KEYS`` when
    ``config.couchbase`` is set; else ``project`` on find node ids. Soft-fails
    with a minimal card when possible.
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
    if not bare:
        return {
            "business": None,
            "business_id": raw_id,
            "source": "none",
            "error": "empty business_id",
            "ai_process_result": False,
            "chat_id": None,
        }

    try:
        cfg = await load_config()
    except Exception as e:
        logger.warning("fetch_business_via_find load_config failed: %s", e)
        return {
            "business": None,
            "business_id": bare,
            "source": "error",
            "error": str(e),
            "ai_process_result": False,
            "chat_id": None,
        }

    find_res = await run_verb_from_config(
        "find",
        {
            "entity_type": "Business",
            "where": {"business_id": bare},
            "limit": 1,
        },
        cfg,
        mode_header="analytics",
    )
    if not find_res.ok:
        err = find_res.error or f"find status {find_res.status}"
        logger.warning("fetch_business_via_find find failed: %s", err)
        return {
            "business": None,
            "business_id": bare,
            "source": "zeus_find",
            "error": err,
            "req_id": find_res.req_id or "",
            "ai_process_result": False,
            "chat_id": None,
        }

    node_ids, doc_keys = _find_result_keys(find_res.body)
    # Prefer stable biz: source keys for N1QL when find items omitted them.
    prefer_key = _biz_doc_key(raw_id, bare)
    if prefer_key and prefer_key not in doc_keys:
        doc_keys = [prefer_key, *doc_keys]

    find_item: dict[str, Any] | None = None
    body = find_res.body if isinstance(find_res.body, dict) else {}
    result = body.get("result") if isinstance(body.get("result"), dict) else body
    if isinstance(result, dict):
        for item in result.get("items") or []:
            if isinstance(item, dict):
                find_item = item
                break

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

    keys_for_n1ql = [k for k in doc_keys if k.startswith("biz:")] or (
        [prefer_key] if prefer_key.startswith("biz:") else []
    )
    if keys_for_n1ql and cb is not None:
        try:
            rows = await n1ql_hydrate_keys(
                cb,
                bucket,
                scope,
                collection,
                keys_for_n1ql[:1],
                fields=_BUSINESS_N1QL_FIELDS,
            )
            if rows:
                source = "zeus_find+n1ql"
                sources.append("n1ql_hydrate")
        except Exception as e:
            logger.warning("fetch_business_via_find n1ql hydrate failed: %s", e)

    if not rows and node_ids:
        proj = await run_verb_from_config(
            "project",
            {"ids": node_ids[:1], "fields": list(_BUSINESS_PROJECT_FIELDS)},
            cfg,
            mode_header="analytics",
        )
        if proj.ok:
            rows = _project_rows(proj.body)
            if rows:
                source = "zeus_find+project"
                sources.append("zeus_project")

    card: dict[str, str] | None = None
    if rows:
        card = _row_to_business_card(rows[0], fallback_id=prefer_key or bare)
    if not card and find_item:
        card = _card_from_find_item(find_item, raw_id=raw_id, bare=bare)

    if card:
        from local_guide.business_images import apply_local_images

        apply_local_images(card)

    return {
        "business": card,
        "business_id": bare,
        "source": source,
        "sources": sources,
        "req_id": find_res.req_id or "",
        "ai_process_result": False,
        "chat_id": None,
        "error": None if card else "business not found",
    }


async def get_business(business_id: str, chat_id: str | None = None) -> dict:
    """Return a business card via cache or direct V2 ``find`` (no LLM).

    ``chat_id`` is accepted for API compatibility but **ignored** — detail seed
    never binds discovery multi-turn history (see session isolation guide).
    """
    from local_guide.business_images import apply_local_images

    # Client may still send the landing/results chat_id; never reuse it here.
    _ = chat_id

    cached = find_cached_business(business_id)
    if cached:
        apply_local_images(cached)
        return {
            "business": cached,
            "chat_id": None,
            "source": "cache",
            "ai_process_result": False,
        }

    fetched = await fetch_business_via_find(business_id)
    card = fetched.get("business")
    if isinstance(card, dict) and card.get("name"):
        return {
            "business": card,
            "chat_id": None,
            "source": fetched.get("source") or "zeus_find",
            "sources": fetched.get("sources") or [],
            "req_id": fetched.get("req_id") or "",
            "ai_process_result": False,
            "error": None,
        }

    # Soft placeholder so deep-links still render chrome; SPA can show empty fields.
    raw = (business_id or "").strip()
    bare = normalize_yelp_business_id(raw)
    placeholder = {
        "name": raw or bare or "Business",
        "description": "",
        "image": "",
        "business_id": _biz_doc_key(raw, bare) or raw,
    }
    apply_local_images(placeholder)
    return {
        "business": placeholder,
        "chat_id": None,
        "source": fetched.get("source") or "none",
        "sources": fetched.get("sources") or [],
        "req_id": fetched.get("req_id") or "",
        "ai_process_result": False,
        "error": fetched.get("error") or "business not found",
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
