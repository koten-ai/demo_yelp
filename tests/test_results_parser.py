from local_guide.results_parser import extract_businesses, zeus_data_to_results


def test_zeus_data_maps_yelp_business():
    rows = [
        {
            "entity_type": "Business",
            "business_id": "b1",
            "name": "Lumina Roasters",
            "stars": 4.8,
            "review_count": 1284,
            "categories": "Coffee & Tea, Bakeries",
            "city": "Philadelphia",
            "state": "PA",
            "address": "123 Main",
            "latitude": 39.95,
            "longitude": -75.16,
            "is_open": 1,
            "attributes": {"RestaurantsPriceRange2": "2"},
            "description": "Great coffee",
        }
    ]
    cards = zeus_data_to_results(rows)
    assert len(cards) == 1
    c = cards[0]
    assert c["name"] == "Lumina Roasters"
    assert c["business_id"] == "b1"
    assert c["rating"] == "4.8"
    assert c["review_count"] == "1284"
    assert "description" in c and "image" in c
    assert c["latitude"] == "39.95"
    assert c["longitude"] == "-75.16"
    assert c["price"] == "$$"
    assert c["is_open"] == "true"
    assert "Coffee" in c["categories"]


def test_doc_key_business_id():
    rows = [{"name": "X", "doc_key": "biz:yelp:abc99", "stars": 5}]
    cards = zeus_data_to_results(rows)
    assert cards[0]["business_id"] == "abc99"


def test_prefers_biz_doc_key_over_file_node_id():
    """Ask AI / project rows: id+node_id are file::; durable key is doc_key biz:…"""
    rows = [
        {
            "name": "Green Locus",
            "city": "Tampa",
            "state": "FL",
            "stars": 5,
            "review_count": 38,
            "doc_key": "biz:ZuM1vcZ_ObCjCCGweYzItg",
            "id": "file::012bc3e2a9b379b9",
            "node_id": "file::012bc3e2a9b379b9",
            "is_open": 1,
            "latitude": 28.0576236,
            "longitude": -82.5821822,
        }
    ]
    cards = zeus_data_to_results(rows)
    assert len(cards) == 1
    assert cards[0]["business_id"] == "biz:ZuM1vcZ_ObCjCCGweYzItg"
    assert not cards[0]["business_id"].startswith("file:")


def test_ignores_graph_id_when_no_doc_key():
    rows = [{"name": "X", "id": "file::deadbeef", "stars": 4}]
    cards = zeus_data_to_results(rows)
    assert len(cards) == 1
    assert "business_id" not in cards[0]


def test_dedupe_by_id():
    rows = [
        {"name": "A", "business_id": "1"},
        {"name": "A", "business_id": "1"},
    ]
    assert len(zeus_data_to_results(rows)) == 1


def test_extract_from_trace():
    trace = {
        "tool_calls": [
            {
                "result_json": {
                    "rows": [
                        {"name": "Cafe One", "city": "Austin", "stars": 4.2},
                    ]
                }
            }
        ]
    }
    cards = extract_businesses(trace)
    assert len(cards) == 1
    assert cards[0]["name"] == "Cafe One"
