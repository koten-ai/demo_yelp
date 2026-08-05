import pytest


def test_health(client):
    from importlib.metadata import version as pkg_version

    from local_guide import __version__ as app_pkg_version

    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    # Header chrome: app (local-guide) and Zeus client are separate fields/labels.
    try:
        expected_app = pkg_version("local-guide")
    except Exception:
        expected_app = app_pkg_version
    assert data["app_version"] == expected_app
    assert data["zeus_client_version"] == pkg_version("kotenai-zeus-client")
    # Distinct fields so UI can label them separately (values may match by chance).
    assert "app_version" in data and "zeus_client_version" in data
    assert isinstance(data["app_version"], str) and data["app_version"]
    assert isinstance(data["zeus_client_version"], str) and data["zeus_client_version"]


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
    captured = {}

    async def fake_search(query, chat_id=None, *, ai_process_result=False):
        captured["ai_process_result"] = ai_process_result
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
            "ai_process_result": ai_process_result,
        }

    monkeypatch.setattr("local_guide.app.run_search", fake_search)
    res = client.post("/api/search", json={"query": "coffee"})
    assert res.status_code == 200
    data = res.json()
    assert data["chat_id"].startswith("yelp_")
    assert data["results"][0]["name"] == "Cafe"
    assert "trace" in data
    # Landing/results default: cheap path
    assert captured["ai_process_result"] is False
    assert data["ai_process_result"] is False


@pytest.mark.asyncio
async def test_search_ask_ai_enables_insight(monkeypatch, client):
    captured = {}

    async def fake_search(query, chat_id=None, *, ai_process_result=False):
        captured["ai_process_result"] = ai_process_result
        return {
            "chat_id": chat_id or "yelp_askai",
            "query": query,
            "answer": "Insight answer",
            "structured_answer": None,
            "structured_response": {
                "answer": "Insight answer",
                "zeus_data": [],
                "warnings": [],
            },
            "results": [],
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
            "ai_process_result": ai_process_result,
        }

    monkeypatch.setattr("local_guide.app.run_search", fake_search)
    res = client.post(
        "/api/search",
        json={"query": "quiet cafes", "ai_process_result": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert captured["ai_process_result"] is True
    assert data["ai_process_result"] is True
