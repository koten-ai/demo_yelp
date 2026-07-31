#!/usr/bin/env python3
"""Rebuild business-images/manifest.json and stamp Couchbase docs with image paths.

Run from demo_yelp root after images are generated:

    python3 scripts/finalize_business_images.py

Optional CDN / Spaces absolute URLs (no trailing slash)::

    export BUSINESS_IMAGES_BASE_URL=https://koten-yelp-demo-photos.nyc3.cdn.digitaloceanspaces.com/business-images
    python3 scripts/finalize_business_images.py

Couchbase query defaults (override as needed)::

    COUCHBASE_QUERY_URL=http://127.0.0.1:8093
    COUCHBASE_USERNAME=Administrator
    COUCHBASE_PASSWORD=password
    YELP_BUCKET=yelp-data
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from local_guide.business_images import (  # noqa: E402
    IMAGES_ROOT,
    get_url_prefix,
    load_catalog,
    public_image_url,
    write_manifest,
)


def rebuild_manifest() -> dict:
    businesses: dict[str, dict] = {}
    if not IMAGES_ROOT.is_dir():
        raise SystemExit(f"missing {IMAGES_ROOT}")
    for child in sorted(IMAGES_ROOT.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        bid = child.name
        files = sorted(
            p.name
            for p in child.iterdir()
            if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )
        if not files:
            continue
        urls = [public_image_url(bid, f) for f in files]
        businesses[bid] = {
            "business_id": bid,
            "image": urls[0],
            "images": urls,
            "files": files,
        }
    write_manifest(businesses)
    return businesses


def n1ql(statement: str, *, args: list | None = None) -> dict:
    body: dict = {"statement": statement}
    if args is not None:
        body["args"] = args
    data = json.dumps(body).encode()
    query_url = (
        os.environ.get("COUCHBASE_QUERY_URL") or "http://127.0.0.1:8093"
    ).rstrip("/")
    req = urllib.request.Request(
        f"{query_url}/query/service",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    user = os.environ.get("COUCHBASE_USERNAME") or "Administrator"
    password = os.environ.get("COUCHBASE_PASSWORD") or "password"
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def update_couchbase(businesses: dict[str, dict]) -> tuple[int, int]:
    bucket = os.environ.get("YELP_BUCKET") or "yelp-data"
    ok = fail = 0
    for bid, meta in businesses.items():
        image = meta["image"]
        images = meta["images"]
        img_json = json.dumps(image)
        imgs_json = json.dumps(images)
        key = bid.replace("\\", "\\\\").replace('"', '\\"')
        stmt2 = (
            f"UPDATE `{bucket}`._default._default AS b USE KEYS \"{key}\" "
            f"SET b.image = {img_json}, b.images = {imgs_json}, "
            f"b.image_paths = {imgs_json}, b.photo = {img_json} "
            f"RETURNING META(b).id AS id"
        )
        try:
            res2 = n1ql(stmt2)
            if res2.get("status") == "success":
                ok += 1
            else:
                fail += 1
                print("fail", bid, res2.get("errors"), file=sys.stderr)
        except Exception as e:
            fail += 1
            print("fail", bid, e, file=sys.stderr)
    return ok, fail


def main() -> int:
    prefix = get_url_prefix()
    print(f"url_prefix={prefix}")
    businesses = rebuild_manifest()
    cat = load_catalog(force=True)
    print(f"manifest businesses={len(businesses)} catalog={len(cat)}")
    complete = sum(1 for v in businesses.values() if len(v.get("images") or []) >= 3)
    print(f"with>=3 images: {complete}")
    if os.environ.get("FINALIZE_SKIP_COUCHBASE", "").strip() in {"1", "true", "yes"}:
        print("skipping couchbase (FINALIZE_SKIP_COUCHBASE)")
        return 0
    ok, fail = update_couchbase(businesses)
    print(f"couchbase updated ok={ok} fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
