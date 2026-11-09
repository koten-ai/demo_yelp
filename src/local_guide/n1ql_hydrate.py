"""Direct Couchbase Query hydrate for detail cards. Zeus verbs do not return source text."""
from __future__ import annotations

import json
import logging
import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger("local_guide.n1ql_hydrate")

_YELP_DOC_PREFIX = "biz:yelp:"


def business_doc_keys(business_id: str) -> list[str]:
    """Source keys for one business card.

    Live yelp-demo documents are ``biz:yelp:<id>``. A card that already carries
    a different ``biz:`` key is tried after that live key.
    """
    bid = (business_id or "").strip()
    if not bid:
        return []
    own = bid if bid.startswith("biz:") else ""
    if bid.startswith(_YELP_DOC_PREFIX):
        bare = bid[len(_YELP_DOC_PREFIX) :].strip()
    elif own:
        bare = bid[4:].strip()
    else:
        bare = bid
    keys: list[str] = []
    if bare:
        keys.append(f"{_YELP_DOC_PREFIX}{bare}")
    if own and own not in keys:
        keys.append(own)
    return keys


def _coord_text(val: Any) -> str:
    if val is None or isinstance(val, bool):
        return ""
    if isinstance(val, float):
        if val != val:
            return ""
        return str(val)
    if isinstance(val, int):
        return str(val)
    text = str(val).strip()
    if text.lower() in {"", "none", "null", "nan"}:
        return ""
    return text


def apply_coordinate_rows(cards: list[dict[str, Any]], rows: list[dict[str, Any]]) -> int:
    """Copy latitude and longitude from source rows onto cards that lack both.

    Rows are matched by ``doc_key`` only. For each card, the first
    ``business_doc_keys`` entry that has both coordinates wins.
    """
    by_key: dict[str, tuple[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        doc_key = str(row.get("doc_key") or "").strip()
        lat = _coord_text(row.get("latitude"))
        lon = _coord_text(row.get("longitude"))
        if not doc_key or not lat or not lon:
            continue
        by_key.setdefault(doc_key, (lat, lon))

    filled = 0
    for card in cards:
        if not isinstance(card, dict):
            continue
        if _coord_text(card.get("latitude")) and _coord_text(card.get("longitude")):
            continue
        bid = str(card.get("business_id") or "").strip()
        if not bid:
            continue
        for key in business_doc_keys(bid):
            hit = by_key.get(key)
            if hit is None:
                continue
            card["latitude"], card["longitude"] = hit
            filled += 1
            break
    return filled


@dataclass(frozen=True)
class QueryService:
    query_url: str
    username: str
    password: str


def query_service_from_env() -> QueryService | None:
    """Query service from COUCHBASE_QUERY_URL. Missing URL means skip hydrate."""
    url = (os.environ.get("COUCHBASE_QUERY_URL") or "").strip()
    if not url:
        return None
    return QueryService(
        query_url=url.rstrip("/"),
        username=(os.environ.get("COUCHBASE_USERNAME") or "Administrator").strip(),
        password=os.environ.get("COUCHBASE_PASSWORD") or "",
    )


async def n1ql_query(
    cb: QueryService,
    statement: str,
    *,
    timeout_s: float = 15.0,
) -> list[Any] | None:
    """POST one statement. None means the service did not return a result list."""
    url = f"{cb.query_url.rstrip('/')}/query/service"
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as http:
            res = await http.post(
                url,
                data={"statement": statement},
                auth=(cb.username, cb.password),
            )
    except httpx.HTTPError as exc:
        logger.warning("n1ql unreachable %s: %s", url, type(exc).__name__)
        return None
    if res.status_code != 200:
        logger.warning("n1ql status=%s", res.status_code)
        return None
    try:
        body = res.json()
    except Exception:
        logger.warning("n1ql response was not JSON")
        return None
    rows = body.get("results") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        logger.warning("n1ql response has no result list")
        return None
    return rows


async def n1ql_hydrate_keys(
    cb: QueryService,
    bucket: str,
    scope: str,
    collection: str,
    keys: Sequence[str],
    *,
    fields: Sequence[str] = (),
    timeout_s: float = 15.0,
) -> list[dict[str, Any]]:
    """``USE KEYS`` hydrate. Returns rows in server order."""
    if not keys:
        return []
    field_sql = ", ".join(f"`{f}`" if not str(f).startswith("`") else str(f) for f in fields)
    if "doc_key" not in fields and "META().id" not in field_sql:
        select_list = f"META().id AS doc_key, {field_sql}" if field_sql else "META().id AS doc_key"
    else:
        select_list = field_sql or "META().id AS doc_key"
    keys_lit = ", ".join(json.dumps(k) for k in keys)
    statement = (
        f"SELECT {select_list} "
        f"FROM `{bucket}`.`{scope}`.`{collection}` "
        f"USE KEYS [{keys_lit}]"
    )
    rows = await n1ql_query(cb, statement, timeout_s=timeout_s)
    if not rows:
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        doc_key = str(row.get("doc_key") or "").strip()
        if doc_key:
            row.setdefault("business_id", doc_key)
            row.setdefault("id", doc_key)
        out.append(row)
    return out
