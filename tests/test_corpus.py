"""Corpus size resolution for search-loader copy."""
from __future__ import annotations

import pytest

from local_guide import corpus as corpus_mod


@pytest.fixture(autouse=True)
def _clear_cache():
    corpus_mod.clear_corpus_cache()
    yield
    corpus_mod.clear_corpus_cache()


def test_admin_base_url_from_zeus_url(monkeypatch):
    monkeypatch.delenv("ZEUS_ADMIN_URL", raising=False)
    monkeypatch.delenv("ZEUS_HUB_URL", raising=False)
    monkeypatch.delenv("ZEUS_URL", raising=False)
    assert (
        corpus_mod.admin_base_url("http://host.docker.internal:8080")
        == "http://host.docker.internal:9091"
    )


def test_admin_base_url_explicit(monkeypatch):
    monkeypatch.setenv("ZEUS_ADMIN_URL", "http://hub.example:9091/")
    assert corpus_mod.admin_base_url("http://ignored:8080") == "http://hub.example:9091"


@pytest.mark.asyncio
async def test_resolve_prefers_config_override(monkeypatch):
    monkeypatch.setattr(
        corpus_mod,
        "read_app_config",
        lambda: {
            "ui": {"business_count": 10_000_000, "corpus_label": "businesses"},
            "default_sample": "yelp",
            "samples": {"yelp": {"bucket": "yelp-data"}},
        },
    )

    async def boom(*_a, **_k):
        raise AssertionError("should not hit live admin when config override set")

    monkeypatch.setattr(corpus_mod, "fetch_collection_count", boom)
    out = await corpus_mod.resolve_search_corpus(force=True)
    assert out["business_count"] == 10_000_000
    assert out["corpus_label"] == "businesses"
    assert out["corpus_source"] == "config"


@pytest.mark.asyncio
async def test_resolve_uses_live_collection_counts(monkeypatch):
    monkeypatch.setattr(
        corpus_mod,
        "read_app_config",
        lambda: {
            "default_sample": "yelp",
            "samples": {
                "yelp": {
                    "bucket": "yelp-data",
                    "scope": "_default",
                    "collection": "_default",
                }
            },
            "ui": {"corpus_label": "businesses"},
        },
    )

    async def fake_fetch(bucket, scope, collection, **_k):
        assert bucket == "yelp-data"
        assert scope == "_default"
        assert collection == "_default"
        return 161_237

    monkeypatch.setattr(corpus_mod, "fetch_collection_count", fake_fetch)
    out = await corpus_mod.resolve_search_corpus(force=True)
    assert out["business_count"] == 161_237
    assert out["corpus_source"] == "zeus_admin"


def test_health_includes_business_count(monkeypatch, client):
    async def fake_corpus(*, force: bool = False):
        return {
            "business_count": 161_237,
            "corpus_label": "businesses",
            "corpus_source": "zeus_admin",
        }

    monkeypatch.setattr("local_guide.app.resolve_search_corpus", fake_corpus)
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["business_count"] == 161_237
    assert data["corpus_label"] == "businesses"
    assert data["corpus_source"] == "zeus_admin"
    assert "zeus_client_version" in data
