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
    url = f"{cb.query_url.rstrip('/')}/query/service"
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as http:
            res = await http.post(
                url,
                data={"statement": statement},
                auth=(cb.username, cb.password),
            )
    except httpx.HTTPError as e:
        logger.warning("n1ql unreachable %s: %s", url, e)
        return []
    if res.status_code != 200:
        logger.warning("n1ql status=%s body=%s", res.status_code, (res.text or "")[:240])
        return []
    try:
        body = res.json()
    except Exception:
        return []
    rows = body.get("results") if isinstance(body, dict) else None
    if not isinstance(rows, list):
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
