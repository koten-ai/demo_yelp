"""Shared pytest fixtures."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    """FastAPI test client with lifespan side effects disabled."""
    async def _noop_lifespan(app):
        yield

    monkeypatch.setattr("local_guide.app.lifespan", _noop_lifespan)

    import local_guide.app as app_module

    # Recreate app with patched lifespan
    app = app_module.create_app()
    with TestClient(app) as c:
        yield c
