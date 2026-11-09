"""Corpus size resolution for search-loader copy."""
from __future__ import annotations

import pytest

from local_guide import corpus as corpus_mod


@pytest.fixture(autouse=True)
def _clear_cache():
    corpus_mod.clear_corpus_cache()
    yield
    corpus_mod.clear_corpus_cache()


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
        raise AssertionError("should not query the database when a count is configured")

    monkeypatch.setattr(corpus_mod, "fetch_business_count", boom)
    out = await corpus_mod.resolve_search_corpus(force=True)
    assert out["business_count"] == 10_000_000
    assert out["corpus_label"] == "businesses"
    assert out["corpus_source"] == "config"


@pytest.mark.asyncio
async def test_resolve_counts_business_documents(monkeypatch):
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

    async def fake_business(bucket, scope, collection):
        assert bucket == "yelp-data"
        assert scope == "_default"
        assert collection == "_default"
        return 2251

    monkeypatch.setattr(corpus_mod, "fetch_business_count", fake_business)
    out = await corpus_mod.resolve_search_corpus(force=True)
    assert out["business_count"] == 2251
    assert out["corpus_source"] == "couchbase"


@pytest.mark.asyncio
async def test_fetch_business_count_reads_the_raw_count(monkeypatch):
    from local_guide.n1ql_hydrate import QueryService

    calls: list[tuple[str, str]] = []

    async def fake_query(cb, statement, **_k):
        calls.append((cb.username, statement))
        return [2251]

    monkeypatch.setattr(corpus_mod, "n1ql_query", fake_query)
    monkeypatch.setattr(
        corpus_mod,
        "query_service_from_env",
        lambda: QueryService("http://query.example", "user", "secret"),
    )
    assert await corpus_mod.fetch_business_count("yelp-demo", "_default", "_default") == 2251
    assert calls[0][0] == "user"
    assert 'WHERE `type` = "Business"' in calls[0][1]
    assert await corpus_mod.fetch_business_count("bad name", "_default", "_default") is None
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_fetch_business_count_rejects_a_non_integer_row(monkeypatch):
    from local_guide.n1ql_hydrate import QueryService

    async def fake_query(*_a, **_k):
        return [{"n": 2251}]

    monkeypatch.setattr(corpus_mod, "n1ql_query", fake_query)
    monkeypatch.setattr(
        corpus_mod,
        "query_service_from_env",
        lambda: QueryService("http://query.example", "user", "secret"),
    )
    assert await corpus_mod.fetch_business_count("yelp-demo", "_default", "_default") is None


@pytest.mark.asyncio
async def test_n1ql_query_rejects_a_non_json_body(monkeypatch, caplog):
    from local_guide import n1ql_hydrate

    class _Res:
        status_code = 200

        def json(self):
            raise ValueError("not json")

    class _Client:
        def __init__(self, *_a, **_k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_a):
            return False

        async def post(self, _url, data, auth):
            assert auth[0] == "user"
            assert "COUNT" in data["statement"]
            return _Res()

    monkeypatch.setattr(n1ql_hydrate.httpx, "AsyncClient", _Client)
    caplog.set_level("WARNING")
    rows = await n1ql_hydrate.n1ql_query(
        n1ql_hydrate.QueryService("http://query.example", "user", "secret"),
        "SELECT RAW COUNT(*)",
    )
    assert rows is None
    assert "n1ql response was not JSON" in caplog.text


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
