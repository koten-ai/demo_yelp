"""In-memory chat store + JSONL persistence for multi-turn local searches."""
from __future__ import annotations

import asyncio
import json
import os
import time
from copy import deepcopy
from pathlib import Path

from local_guide.paths import PROJECT_ROOT

CHAT_LOG_PATH = Path(
    os.environ.get("CHAT_LOG_PATH") or (PROJECT_ROOT / "data" / "chats.jsonl")
)

CHATS: dict[str, dict] = {}

_CHAT_LOCKS: dict[str, asyncio.Lock] = {}
_CHAT_LOCKS_GUARD = asyncio.Lock()


async def chat_lock(chat_id: str) -> asyncio.Lock:
    async with _CHAT_LOCKS_GUARD:
        lk = _CHAT_LOCKS.get(chat_id)
        if lk is None:
            lk = asyncio.Lock()
            _CHAT_LOCKS[chat_id] = lk
        return lk


def append_chat_event(event, **payload):
    """Append one chat-store event to the local JSONL file."""
    row = {"event": event, "at": time.time(), **payload}
    CHAT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHAT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def load_chats_from_jsonl():
    """Replay chats.jsonl into CHATS, creating an empty file if missing."""
    CHATS.clear()
    CHAT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHAT_LOG_PATH.touch(exist_ok=True)
    with open(CHAT_LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            event = row.get("event")
            if event == "clear_all":
                CHATS.clear()
            elif event == "delete_chat":
                CHATS.pop(row.get("chat_id"), None)
            elif event == "upsert_chat":
                chat = row.get("chat") or {}
                cid = chat.get("chat_id")
                if cid:
                    CHATS[cid] = chat


async def persist_chat(chat_id):
    chat = deepcopy(CHATS[chat_id])
    chat["chat_id"] = chat_id
    await asyncio.to_thread(append_chat_event, "upsert_chat", chat=chat)
