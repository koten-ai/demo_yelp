"""GET /api/suggest — fast tier typeahead (mocked run_search path)."""
from __future__ import annotations

import pytest

from local_guide.suggest import empty_suggest, hit_to_card


def test_hit_to_card_maps_library_fields():
    card = hit_to_card(
        {
            "id": "biz:abc",
            "name": "J Sushi",
            "subtitle": "★4.5 · Largo · Sushi",
            "city": "Largo",
            "state": "FL",
            "stars": 4.5,
            "review_count": 120,
            "categories": "Sushi Bars",
            "address": "1 Main",
            "source": "zeus_fts+n1ql",
        }
    )
    assert card["business_id"] == "biz:abc"
    assert card["name"] == "J Sushi"
    assert card["rating"] == "4.5"
    assert card["review_count"] == "120"
    assert card["city"] == "Largo"
    assert "Largo" in card["location"]
    assert card["image"] == ""


def test_suggest_short_query_empty(client):
    res = client.get("/api/suggest", params={"q": "s"})
    assert res.status_code == 200
    data = res.json()
    assert data["results"] == []
    assert data["count"] == 0
    assert data["fast_tier"] is True
    assert data["ai_process_result"] is False
    assert data["source"] == "none"


def test_suggest_empty_query(client):
    res = client.get("/api/suggest")
    assert res.status_code == 200
    assert res.json()["results"] == []


@pytest.mark.asyncio
async def test_suggest_mocked_library(monkeypatch, client):
    captured = {}

    async def fake_run(query, *, limit=8):
        captured["query"] = query
        captured["limit"] = limit
        return {
            "query": query,
            "results": [
                {
                    "name": "YO! Sushi",
                    "description": "★4.2 · Sushi",
                    "image": "",
                    "business_id": "biz:yo1",
                    "rating": "4.2",
                    "review_count": "10",
                    "categories": "Sushi",
                    "location": "Reno, NV",
                    "city": "Reno",
                    "state": "NV",
                    "subtitle": "★4.2 · Reno · Sushi",
                    "source": "zeus_fts+n1ql",
                }
            ],
            "count": 1,
            "source": "zeus_fts+n1ql_hydrate",
            "sources": ["zeus_fts", "n1ql_hydrate"],
            "fast_tier": True,
            "ai_process_result": False,
            "error": None,
        }

    monkeypatch.setattr("local_guide.app.run_suggest", fake_run)
    res = client.get("/api/suggest", params={"q": "sushi", "limit": 5})
    assert res.status_code == 200
    data = res.json()
    assert captured["query"] == "sushi"
    assert captured["limit"] == 5
    assert data["count"] == 1
    assert data["results"][0]["name"] == "YO! Sushi"
    assert data["results"][0]["business_id"] == "biz:yo1"
    assert data["fast_tier"] is True
    assert data["source"] == "zeus_fts+n1ql_hydrate"


@pytest.mark.asyncio
async def test_suggest_soft_fail_on_exception(monkeypatch, client):
    async def boom(query, *, limit=8):
        return empty_suggest(query, source="error", error="zeus down")

    monkeypatch.setattr("local_guide.app.run_suggest", boom)
    res = client.get("/api/suggest", params={"q": "pizza"})
    assert res.status_code == 200
    data = res.json()
    assert data["results"] == []
    assert data["source"] == "error"
    assert data["error"] == "zeus down"
