"""FastAPI lifespan: HTTP client, catalog sync, chat reload."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from local_guide.paths import PROJECT_ROOT
from local_guide.zeus_config import client_symbol, configure_zeus_client, load_config

logger = logging.getLogger("local_guide")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_zeus_client()
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)

    init_http = client_symbol("init_http")
    close_http = client_symbol("close_http")
    sync_chat_requests = client_symbol("sync_chat_requests")

    from local_guide.chat_store import load_chats_from_jsonl

    if init_http is not None:
        await init_http()
    load_chats_from_jsonl()
    try:
        cfg = await load_config()
        sync_cfg = cfg.get("chat_requests_sync") or {}
        if sync_cfg.get("on_startup"):
            if sync_chat_requests is None:
                logger.info(
                    "chat_requests sync skipped: zeus_client has no sync_chat_requests"
                )
            else:
                try:
                    result = await sync_chat_requests(cfg)
                    logger.info(
                        "catalog sync synced=%s skipped=%s errors=%s",
                        len(result.synced),
                        len(result.skipped),
                        len(result.errors),
                    )
                except Exception as e:
                    logger.warning("startup chat_requests sync failed: %s", e)
    except Exception as e:
        logger.warning("startup config load failed: %s", e)

    yield
    if close_http is not None:
        await close_http()
