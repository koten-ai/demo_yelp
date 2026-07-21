"""Configure kotenai-zeus-client paths for this app's layout."""
from __future__ import annotations

import os

from local_guide.paths import PROJECT_ROOT


def configure_zeus_client() -> None:
    """Set env vars before any zeus_client import (constants read env at import time)."""
    os.environ.setdefault("ZEUS_CLIENT_CONFIG_DIR", str(PROJECT_ROOT))
    os.environ.setdefault(
        "ZEUS_CHAT_REQUESTS_DIR",
        str(PROJECT_ROOT / "data" / "chat_requests"),
    )
    os.environ.setdefault("CHAT_LOG_PATH", str(PROJECT_ROOT / "data" / "chats.jsonl"))
