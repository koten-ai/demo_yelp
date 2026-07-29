#!/usr/bin/env python3
"""Smoke: dead durable sid rehydrate failure -> same-turn create with match."""
import asyncio
import json
import os
import sys
from pathlib import Path


async def main() -> int:
    cfg_dir = Path(os.environ.get("ZEUS_CLIENT_CONFIG_DIR") or "/app")
    cr_dir = Path(os.environ.get("ZEUS_CHAT_REQUESTS_DIR") or (cfg_dir / "data/chat_requests"))
    os.environ.setdefault("ZEUS_CLIENT_CONFIG_DIR", str(cfg_dir))
    os.environ.setdefault("ZEUS_CHAT_REQUESTS_DIR", str(cr_dir))

    from zeus_client.agent.session_phase import setup_contract_and_session
    from zeus_client.contract_hash import (
        compute_contract_hash,
        extract_stamped_hash,
        resolve_session_contract_hash,
    )
    from zeus_client.http_client import close_http, init_http
    from zeus_client.zeus.auth import resolve_zeus_auth
    from zeus_client.zeus.contracts import resolve_contract_for_scope

    cfg = json.loads((cfg_dir / "config.json").read_text())
    zcfg = cfg["zeus"]
    zeus_url = os.environ.get("ZEUS_URL") or zcfg.get("url")
    sample = (cfg.get("samples") or {}).get(cfg.get("default_sample") or "yelp-demo") or {}
    bucket = sample.get("bucket") or "yelp-demo"
    scope = sample.get("scope") or "_default"
    mode = "analytics"
    chat_req = json.loads(
        (cr_dir / "yelp-demo__default/chat_request_analytics_v2.json").read_text()
    )
    stamped = extract_stamped_hash(chat_req)
    computed = compute_contract_hash(chat_req)
    _cid, bound = resolve_contract_for_scope(zcfg, bucket, scope, mode)
    _sess_h, _ = resolve_session_contract_hash(bound, stamped, computed)
    dead = "sess_20260722T065311655681"

    await init_http()
    try:
        headers, note = await resolve_zeus_auth(zeus_url, zcfg, bucket=bucket, scope=scope)
        print("auth", note)
        trace: dict = {"notes": [], "steps": [], "spans": [], "tool_calls": []}
        result = await setup_contract_and_session(
            zeus_url,
            zcfg,
            bucket,
            scope,
            mode,
            chat_req,
            "Grocery in Philadelphia",
            dead,
            6,
            trace,
            computed,
            stamped,
            headers,
        )
        print("sid", result["sid"])
        print("round", result["this_user_round"])
        print("session", trace.get("session"))
        print("rehydrate", trace.get("session_rehydrate"))
        for n in trace["notes"]:
            s = str(n)
            if any(
                k in s.lower()
                for k in (
                    "rehydrate",
                    "session create",
                    "about to",
                    "contract:",
                    "hash_for",
                    "failed",
                )
            ):
                print("NOTE", s[:240])
        sess = trace.get("session") or {}
        ok = (
            bool(result["sid"])
            and result["sid"] != dead
            and sess.get("contract_status") == "match"
            and sess.get("created") is True
            and sess.get("recovered_from") == dead
        )
        print("RECOVER_OK", ok)
        return 0 if ok else 1
    finally:
        await close_http()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
