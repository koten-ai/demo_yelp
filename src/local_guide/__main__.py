"""CLI entry: python -m local_guide"""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "5000"))
    reload = os.environ.get("ENVIRONMENT") == "dev"
    reload_dirs = None
    if reload:
        dirs = ["/app/src"]
        client_src = (os.environ.get("ZEUS_CLIENT_SRC") or "").strip()
        if client_src and os.path.isdir(client_src):
            dirs.append(client_src)
        reload_dirs = dirs
    uvicorn.run(
        "local_guide.app:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        reload_dirs=reload_dirs,
    )


if __name__ == "__main__":
    main()
