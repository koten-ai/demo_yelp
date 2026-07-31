#!/usr/bin/env python3
"""Download a generated image URL into frontend/public/business-images/<id>/N.png."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--progress", default="")
    ap.add_argument("--meta", default="{}")
    args = ap.parse_args()
    dest = Path(args.path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(args.url, headers={"User-Agent": "demo_yelp-image-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    if len(data) < 1000:
        print(f"too_small:{len(data)}", file=sys.stderr)
        return 2
    dest.write_bytes(data)
    print(f"ok:{dest}:bytes={len(data)}")
    if args.progress:
        meta = json.loads(args.meta or "{}")
        meta.update({"path": str(dest), "url": args.url, "bytes": len(data), "ok": True})
        with open(args.progress, "a", encoding="utf-8") as f:
            f.write(json.dumps(meta) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
