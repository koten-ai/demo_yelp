"""CLI entry: python -m local_guide"""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run(
        "local_guide.app:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("ENVIRONMENT") == "dev",
    )


if __name__ == "__main__":
    main()
