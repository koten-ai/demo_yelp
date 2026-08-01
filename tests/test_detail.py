"""Unit tests for business detail / insight session isolation + reviews verb path."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from local_guide.detail import (
    _isolated_detail_chat_id,
    _review_row_to_ui,
    fetch_business_reviews,
    fetch_business_via_find,
    get_business,
    normalize_yelp_business_id,
    normalize_yelp_user_id,
    parse_insight_answer,
    run_business_insight,
    yelp_user_doc_key,
)


def test_parse_insight_sections():
    answer = """
Summary of reviews.

**The Good**
- Excellent espresso
- Friendly staff

**The Bad**
- Limited seating

**Best For**
- Solo work sessions
- Casual dates
"""
    parsed = parse_insight_answer(answer)
    assert "Excellent espresso" in parsed["the_good"]
    assert "Limited seating" in parsed["the_bad"]
    assert any("work" in x.lower() or "Solo" in x for x in parsed["best_for"])


def test_isolated_detail_chat_id_prefix():
    a = _isolated_detail_chat_id()
    b = _isolated_detail_chat_id()
    assert a.startswith("detail_")
    assert b.startswith("detail_")
    assert a != b


def test_normalize_yelp_business_id_strips_biz_prefix():
    assert normalize_yelp_business_id("biz:abc123") == "abc123"
    assert normalize_yelp_business_id("abc123") == "abc123"
    assert normalize_yelp_business_id("  biz:x  ") == "x"


def test_normalize_yelp_user_id_and_doc_key():
    assert normalize_yelp_user_id("user:abc") == "abc"
    assert normalize_yelp_user_id("abc") == "abc"
    assert yelp_user_doc_key("N-BU6kAHGxm3Fd4hpNHcjA") == "user:N-BU6kAHGxm3Fd4hpNHcjA"
    assert yelp_user_doc_key("user:N-BU6kAHGxm3Fd4hpNHcjA") == "user:N-BU6kAHGxm3Fd4hpNHcjA"


def test_review_row_to_ui_maps_fields():
    row = {
        "user_id": "user_short",
        "stars": 4,
        "text": "Great tacos",
        "date": "2018-01-02 12:00:00",
        "review_id": "revXYZ",
    }
    ui = _review_row_to_ui(row)
    assert ui["author"] == "user_short"
    assert ui["stars"] == "4"
    assert ui["text"] == "Great tacos"
    assert ui["date"].startswith("2018")
    assert ui["review_id"] == "revXYZ"
    assert ui["user_id"] == "user_short"
    assert ui["user_review_count"] == ""


def test_review_row_to_ui_prefers_joined_user_name():
    row = {
        "user_id": "N-BU6kAHGxm3Fd4hpNHcjA",
        "stars": 5,
        "text": "Loved it",
        "date": "2020-01-01",
        "review_id": "r1",
    }
    user = {
        "user_id": "N-BU6kAHGxm3Fd4hpNHcjA",
        "name": "Alex",
        "review_count": 142,
        "average_stars": 3.8,
        "yelping_since": "2012-03-01",
    }
    ui = _review_row_to_ui(row, user=user)
    assert ui["author"] == "Alex"
    assert ui["user_id"] == "N-BU6kAHGxm3Fd4hpNHcjA"
    assert ui["user_review_count"] == "142"
    assert ui["user_average_stars"] == "3.8"
    assert ui["yelping_since"].startswith("2012")


def test_review_row_to_ui_long_user_id_becomes_reviewer():
    row = {
        "user_id": "N-BU6kAHGxm3Fd4hpNHcjA",
        "stars": 1,
        "text": "meh",
        "date": "2011-01-01",
        "review_id": "r2",
    }
    ui = _review_row_to_ui(row)
    assert ui["author"] == "Reviewer"
    assert ui["user_id"] == "N-BU6kAHGxm3Fd4hpNHcjA"


@pytest.mark.asyncio
async def test_get_business_uses_find_not_agent(monkeypatch):
    """Detail seed must not call run_search / discovery chat plane."""
    search_calls: list = []

    async def fake_search(*args, **kwargs):
        search_calls.append((args, kwargs))
        raise AssertionError("get_business must not call run_search")

    async def fake_find(business_id: str):
        assert business_id == "1dSKEitDDgIkaApe6UNMSA"
        return {
            "business": {
                "name": "The Pepper Pott",
                "description": "Caribbean",
                "image": "",
                "business_id": "biz:1dSKEitDDgIkaApe6UNMSA",
                "city": "Tampa",
                "state": "FL",
                "rating": "4.5",
            },
            "business_id": "1dSKEitDDgIkaApe6UNMSA",
            "source": "zeus_find+n1ql",
            "sources": ["zeus_find", "n1ql_hydrate"],
            "req_id": "req_biz",
            "ai_process_result": False,
            "chat_id": None,
            "error": None,
        }

    monkeypatch.setattr("local_guide.detail.run_search", fake_search)
    monkeypatch.setattr("local_guide.detail.fetch_business_via_find", fake_find)
    monkeypatch.setattr("local_guide.detail.find_cached_business", lambda _bid: None)

    out = await get_business(
        "1dSKEitDDgIkaApe6UNMSA",
        chat_id="yelp_discovery_shared",
    )
    assert search_calls == []
    assert out["business"]["name"] == "The Pepper Pott"
    assert out["source"] == "zeus_find+n1ql"
    assert out["chat_id"] is None
    assert out["ai_process_result"] is False
    assert out.get("req_id") == "req_biz"


@pytest.mark.asyncio
async def test_get_business_prefers_cache(monkeypatch):
    async def boom(_bid):
        raise AssertionError("should not find when cache hits")

    monkeypatch.setattr(
        "local_guide.detail.find_cached_business",
        lambda _bid: {
            "name": "Cached Cafe",
            "business_id": "biz:c1",
            "description": "",
            "image": "",
        },
    )
    monkeypatch.setattr("local_guide.detail.fetch_business_via_find", boom)
    out = await get_business("biz:c1", chat_id="ignored")
    assert out["source"] == "cache"
    assert out["business"]["name"] == "Cached Cafe"
    assert out["chat_id"] is None


@pytest.mark.asyncio
async def test_insight_ignores_discovery_chat_id(monkeypatch):
    captured: dict = {}

    async def fake_search(query, chat_id=None, *, ai_process_result=False):
        captured["chat_id"] = chat_id
        return {
            "chat_id": chat_id,
            "answer": "**The Good**\n- Great food\n\n**The Bad**\n- Busy\n\n**Best For**\n- Lunch",
            "results": [],
            "structured_response": {"zeus_data": []},
            "trace": {"steps": []},
            "tool_order": {"v1": [], "v2": []},
            "session_id": "sess_insight",
            "session_round": 1,
        }

    async def fake_reviews(business_id, *, limit=20):
        return {
            "business_id": business_id,
            "reviews": [
                {
                    "author": "Reviewer",
                    "stars": "5",
                    "text": "Loved it",
                    "date": "2020-01-01",
                }
            ],
            "count": 1,
            "source": "zeus_find+n1ql",
        }

    monkeypatch.setattr("local_guide.detail.run_search", fake_search)
    monkeypatch.setattr("local_guide.detail.fetch_business_reviews", fake_reviews)
    monkeypatch.setattr(
        "local_guide.detail.find_cached_business",
        lambda _bid: {"name": "The Pepper Pott", "business_id": "biz:x"},
    )

    out = await run_business_insight("biz:x", chat_id="yelp_from_landing")
    assert captured["chat_id"] != "yelp_from_landing"
    assert str(captured["chat_id"]).startswith("detail_")
    assert "Great food" in out["the_good"]
    assert out["session_id"] == "sess_insight"
    assert out["reviews"][0]["text"] == "Loved it"
    assert out["reviews_source"] == "zeus_find+n1ql"


@pytest.mark.asyncio
async def test_api_insight_ignores_body_chat_id(monkeypatch, client):
    captured: dict = {}

    async def fake_insight(business_id, chat_id=None):
        captured["business_id"] = business_id
        captured["chat_id_arg"] = chat_id
        return {
            "business_id": business_id,
            "business": None,
            "summary": "ok",
            "the_good": [],
            "the_bad": [],
            "best_for": [],
            "reviews": [],
            "chat_id": "detail_abc",
            "trace": {},
            "answer": "ok",
            "session_id": "sess_x",
            "session_round": 1,
        }

    monkeypatch.setattr("local_guide.app.run_business_insight", fake_insight)
    res = client.post(
        "/api/business/biz%3Aabc/insight",
        json={"chat_id": "yelp_should_not_bind_session"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["chat_id"] == "detail_abc"
    # API still forwards the body value into the helper; helper isolates internally.
    assert captured["chat_id_arg"] == "yelp_should_not_bind_session"


@pytest.mark.asyncio
async def test_fetch_business_via_find_uses_find_verb(monkeypatch):
    calls: list[tuple] = []

    class FakeVerb:
        def __init__(self, ok=True, body=None, status=200, req_id="r1", error=""):
            self.ok = ok
            self.body = body
            self.status = status
            self.req_id = req_id
            self.error = error

    async def fake_run_verb_from_config(verb, args, cfg, **kwargs):
        calls.append((verb, args))
        if verb == "find":
            assert args["entity_type"] == "Business"
            assert args["where"]["business_id"] == "-4dYswJy7SPcbcERvitmIg"
            assert args["limit"] == 1
            return FakeVerb(
                body={
                    "result": {
                        "node_ids": ["file::a0b82eb7dd1d0e83"],
                        "items": [
                            {
                                "doc_key": "biz:-4dYswJy7SPcbcERvitmIg",
                                "source": "biz:-4dYswJy7SPcbcERvitmIg",
                                "name": "Pathmark",
                                "type": "Business",
                            }
                        ],
                    }
                }
            )
        if verb == "project":
            return FakeVerb(body={"result": {"rows": []}})
        raise AssertionError(f"unexpected verb {verb}")

    async def fake_load_config():
        return {
            "default_sample": "yelp",
            "samples": {
                "yelp": {
                    "bucket": "yelp-data",
                    "scope": "_default",
                    "collection": "_default",
                }
            },
            "zeus": {"url": "http://127.0.0.1:8080"},
            "couchbase": {
                "query_url": "http://127.0.0.1:8093",
                "username": "Administrator",
                "password": "password",
            },
        }

    async def fake_n1ql(cb, bucket, scope, collection, keys, **kwargs):
        assert keys == ["biz:-4dYswJy7SPcbcERvitmIg"]
        assert bucket == "yelp-data"
        return [
            {
                "doc_key": "biz:-4dYswJy7SPcbcERvitmIg",
                "name": "Pathmark",
                "city": "Philadelphia",
                "state": "PA",
                "stars": 2.5,
                "review_count": 34,
                "categories": "Food, Grocery",
                "address": "3021 Grays Ferry Ave",
                "latitude": 39.9404026,
                "longitude": -75.1932966,
                "business_id": "-4dYswJy7SPcbcERvitmIg",
                "is_open": 0,
                "attributes": {"RestaurantsPriceRange2": "2"},
            }
        ]

    class FakeCB:
        @classmethod
        def from_mapping(cls, raw, **kw):
            return SimpleNamespace(
                query_url="http://127.0.0.1:8093",
                username="Administrator",
                password="password",
            )

    import zeus_client
    import zeus_client.zeus.suggest as suggest_mod

    monkeypatch.setattr(zeus_client, "load_config", fake_load_config)
    monkeypatch.setattr(zeus_client, "run_verb_from_config", fake_run_verb_from_config)
    monkeypatch.setattr(
        zeus_client,
        "resolve_zeus_config",
        lambda cfg: cfg.get("zeus") or {},
    )
    monkeypatch.setattr(zeus_client, "CouchbaseQueryConfig", FakeCB)
    monkeypatch.setattr(suggest_mod, "n1ql_hydrate_keys", fake_n1ql)

    out = await fetch_business_via_find("biz:-4dYswJy7SPcbcERvitmIg")
    assert calls and calls[0][0] == "find"
    assert out["source"] == "zeus_find+n1ql"
    assert out["business"]["name"] == "Pathmark"
    assert out["business"]["city"] == "Philadelphia"
    assert out["business"]["price"] == "$$"
    assert out["business"]["rating"] == "2.5"
    assert out["ai_process_result"] is False
    assert out["error"] is None


@pytest.mark.asyncio
async def test_fetch_business_reviews_uses_find_verb(monkeypatch):
    calls: list[tuple] = []

    class FakeVerb:
        def __init__(self, ok=True, body=None, status=200, req_id="r1", error=""):
            self.ok = ok
            self.body = body
            self.status = status
            self.req_id = req_id
            self.error = error

    async def fake_run_verb_from_config(verb, args, cfg, **kwargs):
        calls.append((verb, args))
        if verb == "find":
            assert args["entity_type"] == "Review"
            assert args["where"]["business_id"] == "bdth7r1brx9yRU7sYwF9jQ"
            return FakeVerb(
                body={
                    "result": {
                        "node_ids": ["file::aaa"],
                        "items": [
                            {
                                "doc_key": "rev:Fo0Io6wKKac9rDzFFAHUzg",
                                "source": "rev:Fo0Io6wKKac9rDzFFAHUzg",
                                "type": "Review",
                            }
                        ],
                    }
                }
            )
        if verb == "project":
            return FakeVerb(body={"result": {"rows": []}})
        raise AssertionError(f"unexpected verb {verb}")

    async def fake_load_config():
        return {
            "default_sample": "yelp",
            "samples": {
                "yelp": {
                    "bucket": "yelp-data",
                    "scope": "_default",
                    "collection": "_default",
                }
            },
            "zeus": {"url": "http://127.0.0.1:8080"},
            "couchbase": {
                "query_url": "http://127.0.0.1:8093",
                "username": "Administrator",
                "password": "password",
            },
        }

    async def fake_n1ql(cb, bucket, scope, collection, keys, **kwargs):
        assert bucket == "yelp-data"
        # First call: review docs; second: user docs.
        if keys and str(keys[0]).startswith("rev:"):
            assert keys == ["rev:Fo0Io6wKKac9rDzFFAHUzg"]
            return [
                {
                    "doc_key": "rev:Fo0Io6wKKac9rDzFFAHUzg",
                    "text": "Ok, so they have GREAT sushi.",
                    "stars": 1,
                    "date": "2011-04-01 13:11:37",
                    "user_id": "N-BU6kAHGxm3Fd4hpNHcjA",
                    "business_id": "bdth7r1brx9yRU7sYwF9jQ",
                    "review_id": "Fo0Io6wKKac9rDzFFAHUzg",
                }
            ]
        if keys and str(keys[0]).startswith("user:"):
            assert keys == ["user:N-BU6kAHGxm3Fd4hpNHcjA"]
            return [
                {
                    "doc_key": "user:N-BU6kAHGxm3Fd4hpNHcjA",
                    "user_id": "N-BU6kAHGxm3Fd4hpNHcjA",
                    "name": "SushiFan",
                    "review_count": 88,
                    "average_stars": 3.2,
                    "yelping_since": "2010-01-01",
                }
            ]
        return []

    class FakeCB:
        @classmethod
        def from_mapping(cls, raw, **kw):
            return SimpleNamespace(
                query_url="http://127.0.0.1:8093",
                username="Administrator",
                password="password",
            )

    import zeus_client
    import zeus_client.zeus.suggest as suggest_mod

    monkeypatch.setattr(zeus_client, "load_config", fake_load_config)
    monkeypatch.setattr(zeus_client, "run_verb_from_config", fake_run_verb_from_config)
    monkeypatch.setattr(
        zeus_client,
        "resolve_zeus_config",
        lambda cfg: cfg.get("zeus") or {},
    )
    monkeypatch.setattr(zeus_client, "CouchbaseQueryConfig", FakeCB)
    monkeypatch.setattr(suggest_mod, "n1ql_hydrate_keys", fake_n1ql)

    out = await fetch_business_reviews("biz:bdth7r1brx9yRU7sYwF9jQ", limit=5)
    assert calls and calls[0][0] == "find"
    assert out["count"] == 1
    assert out["source"] == "zeus_find+n1ql+users"
    assert "n1ql_user_hydrate" in (out.get("sources") or [])
    assert "GREAT sushi" in out["reviews"][0]["text"]
    assert out["reviews"][0]["author"] == "SushiFan"
    assert out["reviews"][0]["user_id"] == "N-BU6kAHGxm3Fd4hpNHcjA"
    assert out["reviews"][0]["user_review_count"] == "88"
    assert out["business_id"] == "bdth7r1brx9yRU7sYwF9jQ"
    assert out["ai_process_result"] is False


@pytest.mark.asyncio
async def test_api_business_reviews_endpoint(monkeypatch, client):
    async def fake_fetch(business_id, *, limit=20):
        return {
            "business_id": business_id,
            "reviews": [
                {
                    "author": "Reviewer",
                    "stars": "5",
                    "text": "Nice",
                    "date": "2021-01-01",
                }
            ],
            "count": 1,
            "source": "zeus_find+n1ql",
            "error": None,
            "ai_process_result": False,
        }

    monkeypatch.setattr("local_guide.app.fetch_business_reviews", fake_fetch)
    res = client.get("/api/business/biz%3Aabc/reviews?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 1
    assert data["reviews"][0]["text"] == "Nice"
    assert data["source"] == "zeus_find+n1ql"


@pytest.mark.asyncio
async def test_api_business_endpoint_find_path(monkeypatch, client):
    async def fake_get(business_id, chat_id=None):
        return {
            "business": {
                "name": "Pathmark",
                "business_id": business_id,
                "description": "",
                "image": "",
            },
            "chat_id": None,
            "source": "zeus_find+n1ql",
            "ai_process_result": False,
            "error": None,
        }

    monkeypatch.setattr("local_guide.app.get_business", fake_get)
    res = client.get("/api/business/biz%3A-4dYswJy7SPcbcERvitmIg")
    assert res.status_code == 200
    data = res.json()
    assert data["business"]["name"] == "Pathmark"
    assert data["source"] == "zeus_find+n1ql"
    assert data["chat_id"] is None
