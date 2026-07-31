"""Corpus size for search-loader copy (\"Searching N businesses…\").

Prefer optional config override, else Zeus Hub collection_counts for the
default sample scope. Cached briefly so /api/health stays cheap.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from local_guide.paths import PROJECT_ROOT

_CACHE_TTL_S = 300.0
_cache: dict[str, Any] = {"ts": 0.0, "payload": None}


def clear_corpus_cache() -> None:
    """Test helper — drop cached corpus stats."""
    _cache["ts"] = 0.0
    _cache["payload"] = None


def _config_path() -> Path:
    root = Path(os.environ.get("ZEUS_CLIENT_CONFIG_DIR", str(PROJECT_ROOT)))
    return root / "config.json"


def read_app_config() -> dict[str, Any]:
    path = _config_path()
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def admin_base_url(zeus_url: str | None = None) -> str:
    """Hub/admin base (collection_counts). ZEUS_ADMIN_URL wins; else :9091 on Zeus host."""
    explicit = (
        os.environ.get("ZEUS_ADMIN_URL")
        or os.environ.get("ZEUS_HUB_URL")
        or ""
    ).strip()
    if explicit:
        return explicit.rstrip("/")

    raw = (zeus_url or os.environ.get("ZEUS_URL") or "").strip()
    if not raw:
        raw = str((read_app_config().get("zeus") or {}).get("url") or "").strip()
    if not raw:
        raw = "http://127.0.0.1:8080"

    parsed = urlparse(raw)
    scheme = parsed.scheme or "http"
    host = parsed.hostname or "127.0.0.1"
    return f"{scheme}://{host}:9091"


def _default_sample(cfg: dict[str, Any]) -> dict[str, Any]:
    name = str(cfg.get("default_sample") or "").strip()
    samples = cfg.get("samples") if isinstance(cfg.get("samples"), dict) else {}
    sample = samples.get(name) if name else None
    if isinstance(sample, dict):
        return sample
    if samples:
        first = next(iter(samples.values()))
        if isinstance(first, dict):
            return first
    return {"bucket": "yelp-demo", "scope": "_default", "collection": "_default"}


def _config_override(cfg: dict[str, Any]) -> tuple[int | None, str]:
    """Return (count, label) from config ui.* or sample.business_count."""
    ui = cfg.get("ui") if isinstance(cfg.get("ui"), dict) else {}
    label = str(ui.get("corpus_label") or "businesses").strip() or "businesses"

    raw = ui.get("business_count")
    if raw is None:
        sample = _default_sample(cfg)
        raw = sample.get("business_count")

    if raw is None or raw == "":
        return None, label
    try:
        return int(raw), label
    except (TypeError, ValueError):
        return None, label


async def fetch_collection_count(
    bucket: str,
    scope: str,
    collection: str,
    *,
    admin_url: str | None = None,
) -> int | None:
    """Live KV item count from Hub GET …/collection_counts."""
    base = (admin_url or admin_base_url()).rstrip("/")
    url = f"{base}/admin/api/scopes/{bucket}/{scope}/collection_counts"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(url)
            if res.status_code != 200:
                return None
            data = res.json()
            counts = data.get("counts") if isinstance(data, dict) else None
            if not isinstance(counts, dict):
                return None
            if collection in counts:
                return int(counts[collection])
            # Sum operator collections; skip Zeus system collections.
            total = 0
            found = False
            for key, value in counts.items():
                name = str(key)
                if name.startswith("zeus_"):
                    continue
                total += int(value)
                found = True
            return total if found else None
    except Exception:
        return None


async def resolve_search_corpus(*, force: bool = False) -> dict[str, Any]:
    """Corpus stats for the SPA search loader.

    Returns:
      business_count: int | None
      corpus_label: str
      corpus_source: \"config\" | \"zeus_admin\" | \"none\"
    """
    now = time.monotonic()
    if (
        not force
        and _cache["payload"] is not None
        and (now - float(_cache["ts"])) < _CACHE_TTL_S
    ):
        return dict(_cache["payload"])

    cfg = read_app_config()
    count, label = _config_override(cfg)
    if count is not None and count >= 0:
        payload = {
            "business_count": count,
            "corpus_label": label,
            "corpus_source": "config",
        }
        _cache["ts"] = now
        _cache["payload"] = payload
        return dict(payload)

    sample = _default_sample(cfg)
    bucket = str(sample.get("bucket") or "yelp-demo")
    scope = str(sample.get("scope") or "_default")
    collection = str(sample.get("collection") or "_default")
    zeus_url = str((cfg.get("zeus") or {}).get("url") or "") or None
    live = await fetch_collection_count(
        bucket,
        scope,
        collection,
        admin_url=admin_base_url(zeus_url),
    )
    payload = {
        "business_count": live,
        "corpus_label": label,
        "corpus_source": "zeus_admin" if live is not None else "none",
    }
    _cache["ts"] = now
    _cache["payload"] = payload
    return dict(payload)
