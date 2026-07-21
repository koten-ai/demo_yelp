from local_guide.detail import parse_insight_answer


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
