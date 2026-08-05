"""Unit tests for search history poison detection and answer fallback."""

from local_guide.search import (
    history_looks_poisoned,
    synthesize_answer_from_results,
    _answer_is_empty,
)


def test_history_empty_not_poisoned():
    assert history_looks_poisoned([]) is False
    assert history_looks_poisoned(None) is False


def test_history_poisoned_by_boundary_errors():
    turns = [
        {
            "role": "tool",
            "content": 'error: internal_error message: "cbstore: resolve trio: targets: unknown boundary: \\"collections\\""',
        },
        {
            "role": "tool",
            "content": 'error: internal_error tool: batch_get_nodes message: "cbstore: resolve trio: targets: unknown boundary: \\"collections\\""',
        },
        {
            "role": "assistant",
            "content": "No businesses found.",
        },
    ]
    assert history_looks_poisoned(turns) is True


def test_history_poisoned_by_canned_no_verifiable():
    turns = [
        {
            "role": "assistant",
            "content": "**No verifiable grocery businesses** due to collection boundary errors.",
            "tool_calls": [],
        },
        {
            "role": "assistant",
            "content": "**No verifiable** parks found.",
        },
    ]
    assert history_looks_poisoned(turns) is True


def test_history_long_is_poisoned():
    turns = [{"role": "user", "content": f"q{i}"} for i in range(50)]
    assert history_looks_poisoned(turns) is True


def test_synthesize_answer():
    results = [
        {"name": "Giant Food Stores", "city": "Philadelphia"},
        {"name": "Pathmark", "city": "Philadelphia"},
    ]
    text = synthesize_answer_from_results("Grocery in Philadelphia", results)
    assert "Giant Food Stores" in text
    assert "Pathmark" in text
    assert "Grocery in Philadelphia" in text


def test_answer_is_empty_markers():
    assert _answer_is_empty("(model returned no content)")
    assert _answer_is_empty("")
    assert _answer_is_empty(None)
    assert not _answer_is_empty("Found 3 places")


def test_user_facing_answer_peels_layer_a_dump():
    from zeus_client import peel_layer_a_summary, user_facing_answer

    dump = (
        "```\n"
        'summary: "Top salon picks in Tampa."\n'
        "confidence: med\n"
        'query_decomposition: {"intent": "salons"}\n'
        'decomposition: {"targets": []}\n'
        "policy_action: answer\n"
        "wish_i_knew: []\n"
        "```"
    )
    assert peel_layer_a_summary(dump) == "Top salon picks in Tampa."
    assert user_facing_answer(dump) == "Top salon picks in Tampa."
