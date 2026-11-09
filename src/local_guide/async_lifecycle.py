"""FastAPI lifespan: chat reload and Zeus runtime shutdown."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from local_guide.paths import PROJECT_ROOT
from local_guide.zeus_config import configure_zeus_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_zeus_client()
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)
    from local_guide.chat_store import load_chats_from_jsonl
    from local_guide.runtime_factory import close_runtime

    load_chats_from_jsonl()
    yield
    await close_runtime()
