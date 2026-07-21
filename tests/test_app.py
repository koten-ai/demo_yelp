import pytest


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_search_rejects_empty_query(client):
    res = client.post("/api/search", json={"query": "  "})
    assert res.status_code == 400
    assert res.json()["error"] == "empty query"


def test_tool_order_returns_versions(client):
    res = client.get("/api/tool-order")
    assert res.status_code == 200
    data = res.json()
    assert "v1" in data and "v2" in data
    assert isinstance(data["v2"], list)
    assert len(data["v2"]) > 0


@pytest.mark.asyncio
async def test_search_mocked(monkeypatch, client):
    async def fake_search(query, chat_id=None):
        return {
            "chat_id": chat_id or "yelp_test123",
            "query": query,
            "answer": "Found places",
            "structured_answer": None,
            "structured_response": {
                "answer": "Found places",
                "zeus_data": [],
                "warnings": [],
            },
            "results": [
                {
                    "name": "Cafe",
                    "description": "Nice",
                    "image": "",
                    "business_id": "b1",
                }
            ],
            "trace": {"steps": []},
            "tool_order": {"v1": [], "v2": ["search", "return"]},
            "target": "yelp-demo/_default/_default",
            "api_version": "v2",
            "mode": "open",
            "model": "test-model",
            "provider": "xai",
            "zeus_connection": "default",
            "zeus_url": "http://localhost:8080",
            "session_id": "sess",
            "session_round": 1,
            "contract_status": "match",
        }

    monkeypatch.setattr("local_guide.app.run_search", fake_search)
    res = client.post("/api/search", json={"query": "coffee"})
    assert res.status_code == 200
    data = res.json()
    assert data["chat_id"].startswith("yelp_")
    assert data["results"][0]["name"] == "Cafe"
    assert "trace" in data
