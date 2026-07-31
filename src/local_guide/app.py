"""FastAPI application factory for LocalAI."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from local_guide.async_lifecycle import lifespan
from local_guide.chat_store import CHATS
from local_guide.corpus import resolve_search_corpus
from local_guide.detail import get_business, run_business_insight
from local_guide.paths import PACKAGE_DIR, PROJECT_ROOT
from local_guide.search import run_search
from local_guide.suggest import DEFAULT_LIMIT, MAX_LIMIT, run_suggest
from local_guide.zeus_config import configure_zeus_client

configure_zeus_client()


class SearchBody(BaseModel):
    query: str = ""
    chat_id: str | None = None
    # False = landing/results cheap path; True = Ask AI insight synthesis (0.2.1+).
    ai_process_result: bool = False


class InsightBody(BaseModel):
    chat_id: str | None = None


def zeus_client_version() -> str:
    """Installed kotenai-zeus-client (zeus_client_python) package version."""
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("kotenai-zeus-client")
        except PackageNotFoundError:
            pass
    except Exception:
        pass
    try:
        import zeus_client

        return str(getattr(zeus_client, "__version__", "unknown") or "unknown")
    except Exception:
        return "unknown"


def create_app() -> FastAPI:
    app = FastAPI(title="LocalAI", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5000",
            "http://127.0.0.1:5000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://zeus-dev.local:5173",
            "http://zeus-dev.local:5000",
            "http://zeus-dev.local:3000",
            "http://zeus-dev.local:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(exc.detail, status_code=exc.status_code)
        return JSONResponse({"error": str(exc.detail)}, status_code=exc.status_code)

    @app.get("/api/health")
    async def health():
        corpus = await resolve_search_corpus()
        return {
            "ok": True,
            # Running zeus_client_python / kotenai-zeus-client — UI chrome source of truth.
            "zeus_client_version": zeus_client_version(),
            # Search loader: "Searching {business_count} {corpus_label}…"
            "business_count": corpus.get("business_count"),
            "corpus_label": corpus.get("corpus_label") or "businesses",
            "corpus_source": corpus.get("corpus_source") or "none",
        }

    @app.post("/api/search")
    async def api_search(body: SearchBody):
        query = (body.query or "").strip()
        if not query:
            raise HTTPException(status_code=400, detail={"error": "empty query"})
        result = await run_search(
            query,
            body.chat_id,
            ai_process_result=bool(body.ai_process_result),
        )
        if result.get("error"):
            status = 502 if "network error" in result["error"] else 400
            raise HTTPException(status_code=status, detail=result)
        return result

    @app.get("/api/suggest")
    async def api_suggest(
        q: str = Query(default=""),
        limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    ):
        """No-LLM typeahead (Zeus FTS + optional N1QL hydrate). Soft-fails empty."""
        return await run_suggest(q, limit=limit)

    @app.get("/api/tool-order")
    async def api_tool_order():
        from zeus_client import build_tool_order

        return build_tool_order(CHATS)

    @app.get("/api/business/{business_id}")
    async def api_business(
        business_id: str,
        chat_id: str | None = Query(default=None),
    ):
        result = await get_business(business_id, chat_id)
        if result.get("error"):
            status = 502 if "network error" in result["error"] else 400
            raise HTTPException(status_code=status, detail=result)
        return result

    @app.post("/api/business/{business_id}/insight")
    async def api_insight(business_id: str, body: InsightBody | None = None):
        body = body or InsightBody()
        result = await run_business_insight(business_id, body.chat_id)
        if result.get("error"):
            status = 502 if "network error" in result["error"] else 400
            raise HTTPException(status_code=status, detail=result)
        return result

    static_dir = PACKAGE_DIR / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    dist = PROJECT_ROOT / "frontend" / "dist"
    if dist.is_dir():
        assets = dist / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/{full_path:path}")
        async def spa(full_path: str):
            if full_path.startswith("api/") or full_path.startswith("static/"):
                raise HTTPException(status_code=404, detail={"error": "not found"})
            candidate = dist / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            index = dist / "index.html"
            if index.is_file():
                return FileResponse(index)
            raise HTTPException(status_code=404, detail={"error": "spa not built"})

    return app


app = create_app()
