from local_guide.answer_parser import parse_markdown_answer, structured_answer_to_results


def test_parse_numbered_business_list():
    answer = (
        "Here are some spots you might like based on quiet mornings.\n\n"
        "1. **Lumina Roasters**\n"
        "- **Location**: Philadelphia, PA\n"
        "- **Description**: Calm coffee shop for deep work\n"
        "- **Rating**: 4.8\n"
        "- **Categories**: Coffee & Tea\n"
        "2. **Brickwork Bean**\n"
        "- **Location**: 1.2 miles away\n"
        "- **Description**: Neighborhood roastery\n"
        "**Tip**: Arrive before 9am for a quiet table.\n"
        "Would you like more options closer to downtown?"
    )
    data = parse_markdown_answer(answer)
    assert data is not None
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Lumina Roasters"
    assert "deep work" in data["items"][0]["description"]
    assert "Tip" in data or data.get("tip")
    cards = structured_answer_to_results(data)
    assert cards[0]["name"] == "Lumina Roasters"
    assert cards[0]["rating"] == "4.8"


def test_parse_embedded_json_block():
    answer = (
        "Results:\n"
        "```json\n"
        '{"items": [{"name": "Test Cafe", "description": "Nice"}]}\n'
        "```"
    )
    data = parse_markdown_answer(answer)
    assert data == {"items": [{"name": "Test Cafe", "description": "Nice"}]}


def test_parse_empty_or_unstructured():
    assert parse_markdown_answer(None) is None
    assert parse_markdown_answer("") is None
    assert parse_markdown_answer("Just a plain sentence with no structure.") is None
