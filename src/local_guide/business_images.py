"""Local AI-generated business image catalog (frontend/public/business-images).

Layout per business id (directory name = Couchbase doc id, e.g. biz:…):

    frontend/public/business-images/<business_id>/{1,2,3}.png
    frontend/public/business-images/manifest.json

Public URL path (colon in id is left as-is; browsers encode on request):

    /business-images/<business_id>/1.png

Optional absolute base (Spaces CDN) via env ``BUSINESS_IMAGES_BASE_URL`` — no
trailing slash; typically ends with ``/business-images``::

    BUSINESS_IMAGES_BASE_URL=https://koten-yelp-demo-photos.nyc3.cdn.digitaloceanspaces.com/business-images
    → https://…/business-images/<business_id>/1.png
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from local_guide.paths import PROJECT_ROOT

IMAGES_ROOT = PROJECT_ROOT / "frontend" / "public" / "business-images"
MANIFEST_PATH = IMAGES_ROOT / "manifest.json"
# Relative default when BUSINESS_IMAGES_BASE_URL is unset.
URL_PREFIX = "/business-images"

_lock = threading.Lock()
_cache: dict[str, list[str]] | None = None
_cache_mtime: float | None = None


def images_root() -> Path:
    return IMAGES_ROOT


def get_url_prefix() -> str:
    """Public URL prefix for image paths (relative path or absolute CDN base)."""
    base = (os.environ.get("BUSINESS_IMAGES_BASE_URL") or "").strip().rstrip("/")
    if base:
        return base
    return URL_PREFIX


def public_image_url(business_id: str, filename: str) -> str:
    bid = (business_id or "").strip()
    name = (filename or "").strip().lstrip("/")
    if not bid or not name:
        return ""
    # Keep id literal in path; static servers decode %3A → ':' on disk lookup.
    return f"{get_url_prefix()}/{bid}/{name}"


def _normalize_image_ref(business_id: str, ref: str) -> str:
    """Turn a filename, relative path, or absolute URL into a public image URL."""
    s = (ref or "").strip()
    if not s:
        return ""
    if s.startswith("http://") or s.startswith("https://"):
        # Keep absolute URLs as-is (already CDN or external).
        return s
    if s.startswith("/"):
        # Relative site path — re-home under current prefix when it is our tree.
        if s.startswith("/business-images/") or s.startswith(URL_PREFIX + "/"):
            rest = s.split("/business-images/", 1)[-1]
            # rest is "<bid>/<file>"
            if "/" in rest:
                bid_part, _, name = rest.partition("/")
                return public_image_url(bid_part or business_id, name)
            return public_image_url(business_id, rest)
        return s
    return public_image_url(business_id, s)


def _scan_disk() -> dict[str, list[str]]:
    """Map business_id → sorted list of public image URLs from on-disk files."""
    out: dict[str, list[str]] = {}
    if not IMAGES_ROOT.is_dir():
        return out
    for child in IMAGES_ROOT.iterdir():
        if not child.is_dir() or child.name.startswith("."):
            continue
        bid = child.name
        files = sorted(
            p.name
            for p in child.iterdir()
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}
        )
        if files:
            out[bid] = [public_image_url(bid, name) for name in files]
    return out


def _load_manifest_file() -> dict[str, list[str]]:
    if not MANIFEST_PATH.is_file():
        return {}
    try:
        raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    businesses = raw.get("businesses") if isinstance(raw, dict) else None
    if not isinstance(businesses, dict):
        return {}
    out: dict[str, list[str]] = {}
    for bid, entry in businesses.items():
        if not isinstance(bid, str) or not bid:
            continue
        images: list[str] = []
        if isinstance(entry, dict):
            imgs = entry.get("images") or entry.get("paths") or []
            primary = entry.get("image") or entry.get("primary")
        elif isinstance(entry, list):
            imgs = entry
            primary = None
        else:
            continue
        if isinstance(imgs, list):
            for item in imgs:
                if isinstance(item, str) and item.strip():
                    u = _normalize_image_ref(bid, item)
                    if u:
                        images.append(u)
        if isinstance(primary, str) and primary.strip():
            p = _normalize_image_ref(bid, primary)
            if p and p not in images:
                images.insert(0, p)
        # de-dupe preserve order
        seen: set[str] = set()
        uniq: list[str] = []
        for u in images:
            if u not in seen:
                seen.add(u)
                uniq.append(u)
        if uniq:
            out[bid] = uniq
    return out


def load_catalog(*, force: bool = False) -> dict[str, list[str]]:
    """Return business_id → [image urls]. Prefers manifest, merges disk scan."""
    global _cache, _cache_mtime
    mtime = None
    if MANIFEST_PATH.is_file():
        try:
            mtime = MANIFEST_PATH.stat().st_mtime
        except OSError:
            mtime = None
    with _lock:
        if not force and _cache is not None and _cache_mtime == mtime:
            return _cache
        catalog = _load_manifest_file()
        disk = _scan_disk()
        for bid, urls in disk.items():
            if bid not in catalog:
                catalog[bid] = urls
            else:
                # Prefer longer/disk-complete lists when files exist
                if len(urls) >= len(catalog[bid]):
                    catalog[bid] = urls
        _cache = catalog
        _cache_mtime = mtime
        return catalog


def images_for(business_id: str | None) -> list[str]:
    bid = (business_id or "").strip()
    if not bid:
        return []
    cat = load_catalog()
    if bid in cat:
        return list(cat[bid])
    # Tolerate missing biz: prefix
    if not bid.startswith("biz:") and f"biz:{bid}" in cat:
        return list(cat[f"biz:{bid}"])
    if bid.startswith("biz:") and bid[4:] in cat:
        return list(cat[bid[4:]])
    return []


def primary_image(business_id: str | None) -> str:
    imgs = images_for(business_id)
    return imgs[0] if imgs else ""


def apply_local_images(card: dict[str, Any] | None) -> dict[str, Any] | None:
    """Mutate a business card with local image / images when catalog has a hit."""
    if not isinstance(card, dict):
        return card
    bid = str(card.get("business_id") or card.get("id") or card.get("doc_key") or "").strip()
    imgs = images_for(bid)
    if not imgs:
        return card
    # Always attach gallery and primary from catalog when we have assets.
    card["images"] = imgs
    card["image"] = imgs[0]
    return card


def apply_local_images_many(cards: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if not cards:
        return []
    out: list[dict[str, Any]] = []
    for c in cards:
        if isinstance(c, dict):
            apply_local_images(c)
            out.append(c)
    return out


def write_manifest(businesses: dict[str, dict[str, Any]]) -> Path:
    """Write manifest.json from id → {name, images: [urls or filenames], ...}."""
    IMAGES_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "url_prefix": get_url_prefix(),
        "businesses": businesses,
    }
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    load_catalog(force=True)
    return MANIFEST_PATH
