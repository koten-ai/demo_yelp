"""FastAPI lifespan: HTTP client, catalog sync, chat reload."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from local_guide.paths import PROJECT_ROOT
from local_guide.zeus_config import configure_zeus_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_zeus_client()
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)

    from zeus_client import close_http, init_http, load_config, logger, sync_chat_requests

    from local_guide.chat_store import load_chats_from_jsonl

    await init_http()
    load_chats_from_jsonl()
    try:
        cfg = await load_config()
        sync_cfg = cfg.get("chat_requests_sync") or {}
        if sync_cfg.get("on_startup"):
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
    await close_http()
