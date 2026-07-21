"""Concrete zeus_data allowlist for the LocalAI yelp demo.

Passed as ``output_schema`` to ``run_agent`` so structured rows are filtered to
fields this app maps into business cards — not full document dumps.
"""
from __future__ import annotations

_CARD = (
    "id",
    "doc_key",
    "entity_type",
    "business_id",
    "name",
    "title",
    "description",
    "summary",
    "brief",
    "overview",
    "snippet",
    "text",
    "categories",
    "category",
    "stars",
    "rating",
    "review_count",
    "review_count_str",
    "address",
    "city",
    "state",
    "postal_code",
    "location",
    "latitude",
    "longitude",
    "lat",
    "lon",
    "lng",
    "hours",
    "is_open",
    "open_now",
    "attributes",
    "price",
    "price_range",
    "RestaurantsPriceRange2",
    "image",
    "image_url",
    "photo",
    "thumbnail",
    "url",
    "website",
    "link",
    "type",
)

_REVIEW = (
    "id",
    "doc_key",
    "entity_type",
    "review_id",
    "business_id",
    "user_id",
    "stars",
    "rating",
    "text",
    "date",
    "useful",
    "funny",
    "cool",
    "name",
)

DEMO_OUTPUT_SCHEMA: dict[str, list[str]] = {
    "Business": list(_CARD),
    "business": list(_CARD),
    "Review": list(_REVIEW),
    "review": list(_REVIEW),
    # Fallbacks if scope brief uses travel-ish labels
    "Hotel": list(_CARD),
    "Destination": list(_CARD),
}
