from local_guide.output_schema import DEMO_OUTPUT_SCHEMA


def test_business_schema_has_card_fields():
    biz = set(DEMO_OUTPUT_SCHEMA["Business"])
    for key in (
        "name",
        "stars",
        "review_count",
        "categories",
        "city",
        "latitude",
        "longitude",
    ):
        assert key in biz


def test_review_schema_has_text_and_stars():
    rev = set(DEMO_OUTPUT_SCHEMA["Review"])
    assert "text" in rev and "stars" in rev


def test_lowercase_aliases_present():
    assert "business" in DEMO_OUTPUT_SCHEMA
    assert "review" in DEMO_OUTPUT_SCHEMA
