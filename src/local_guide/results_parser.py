"""Extract business cards from Zeus agent structured data and traces."""
from __future__ import annotations

import json
from typing import Any

NAME_KEYS = ("name", "title", "business_name")
DESC_KEYS = ("description", "summary", "brief", "overview", "body", "snippet", "text")
IMAGE_KEYS = ("image", "image_url", "photo", "thumbnail", "picture", "img", "cover_image")
BLOB_KEYS = DESC_KEYS + ("content", "document", "payload", "data", "source", "value")
PRICE_KEYS = ("price", "price_range", "rate")
URL_KEYS = ("url", "website", "link", "homepage")
ADDRESS_KEYS = ("address", "location")
RATING_KEYS = ("stars", "rating")
REVIEW_COUNT_KEYS = ("review_count", "review_count_str", "reviewCount")
CATEGORY_KEYS = ("categories", "category")
LAT_KEYS = ("latitude", "lat")
LON_KEYS = ("longitude", "lon", "lng")

MAX_RESULTS = 20

_PRICE_DOLLAR = {1: "$", 2: "$$", 3: "$$$", 4: "$$$$", "1": "$", "2": "$$", "3": "$$$", "4": "$$$$"}


def _first_str(row: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        val = row.get(key)
        if val is None:
            continue
        if isinstance(val, (dict, list)):
            continue
        text = str(val).strip()
        if text and text.lower() not in {"null", "none"}:
            return text
    return ""


def _try_parse_json_obj(val: Any) -> dict[str, Any] | None:
    if isinstance(val, dict):
        return val
    if not isinstance(val, str):
        return None
    text = val.strip()
    if not text or text[0] != "{":
        return None
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _looks_like_entity_blob(data: dict[str, Any]) -> bool:
    keys = set(data)
    has_identity = bool(keys & {"name", "title", "description", "type", "business_id"})
    has_meta = bool(
        keys
        & {
            "address",
            "city",
            "categories",
            "stars",
            "rating",
            "latitude",
            "longitude",
        }
    )
    return has_identity and has_meta


def _is_json_blob_text(text: str) -> bool:
    s = (text or "").strip()
    return bool(s) and s[0] == "{" and _try_parse_json_obj(s) is not None


def _merge_blob_into_row(row: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(row)
    for key in BLOB_KEYS:
        if key not in merged:
            continue
        blob = _try_parse_json_obj(merged.get(key))
        if not blob or not _looks_like_entity_blob(blob):
            continue
        for bk, bv in blob.items():
            if bv is None or bv == "" or bv == "null":
                continue
            existing = merged.get(bk)
            if existing is None or existing == "" or existing == "null":
                merged[bk] = bv
                continue
            if bk == key and isinstance(existing, str) and _is_json_blob_text(existing):
                merged[bk] = bv
            elif bk == key and isinstance(existing, dict):
                merged[bk] = bv
        desc = merged.get("description")
        if isinstance(desc, dict):
            nested = desc.get("description")
            merged["description"] = nested if isinstance(nested, str) else ""
        elif isinstance(desc, str) and _is_json_blob_text(desc):
            inner = _try_parse_json_obj(desc) or {}
            nested = inner.get("description")
            merged["description"] = nested if isinstance(nested, str) else ""
        break
    return merged


def _build_location(row: dict[str, Any]) -> str:
    address = _first_str(row, ADDRESS_KEYS)
    if address and not _is_json_blob_text(address):
        city = _first_str(row, ("city",))
        state = _first_str(row, ("state",))
        if city and city.lower() not in address.lower():
            parts = [address, city, state]
            return ", ".join(p for p in parts if p)
        return address
    parts = [
        _first_str(row, ("city",)),
        _first_str(row, ("state",)),
    ]
    return ", ".join(p for p in parts if p)


def _categories(row: dict[str, Any]) -> str:
    for key in CATEGORY_KEYS:
        val = row.get(key)
        if val is None:
            continue
        if isinstance(val, list):
            parts = [str(x).strip() for x in val if str(x).strip()]
            if parts:
                return ", ".join(parts)
        text = str(val).strip()
        if text and text.lower() not in {"null", "none"}:
            return text
    return ""


def _price_label(row: dict[str, Any]) -> str:
    price = _first_str(row, PRICE_KEYS)
    if price:
        if price in _PRICE_DOLLAR:
            return _PRICE_DOLLAR[price]  # type: ignore[index]
        try:
            n = int(float(price))
            if n in _PRICE_DOLLAR:
                return _PRICE_DOLLAR[n]
        except (TypeError, ValueError):
            pass
        if set(price) <= {"$"}:
            return price
        return price

    attrs = row.get("attributes")
    if isinstance(attrs, str):
        attrs = _try_parse_json_obj(attrs) or {}
    if isinstance(attrs, dict):
        raw = attrs.get("RestaurantsPriceRange2") or attrs.get("price_range")
        if raw is not None and str(raw).strip():
            key: Any = raw
            try:
                key = int(float(raw))
            except (TypeError, ValueError):
                key = str(raw).strip()
            if key in _PRICE_DOLLAR:
                return _PRICE_DOLLAR[key]
            return str(raw).strip()
    # top-level RestaurantsPriceRange2 from schema projection
    raw = row.get("RestaurantsPriceRange2")
    if raw is not None and str(raw).strip():
        try:
            n = int(float(raw))
            if n in _PRICE_DOLLAR:
                return _PRICE_DOLLAR[n]
        except (TypeError, ValueError):
            pass
        return str(raw).strip()
    return ""


def _is_graph_node_id(value: str) -> bool:
    """True for Zeus graph node ids (not Yelp source keys).

    Project rows often set ``id`` / ``node_id`` to ``file::<hash>`` while the
    durable business key lives on ``doc_key`` as ``biz:…``. Using the graph id
    for SPA routes yields ``/business/file%3A%3A…`` and breaks reviews/detail.
    """
    s = (value or "").strip()
    if not s:
        return False
    return s.startswith("file::") or s.startswith("file:") or s.startswith("n_")


def _canonicalize_business_id(value: str) -> str:
    """Normalize source-style business ids; strip legacy ``biz:yelp:`` only."""
    bid = (value or "").strip()
    if not bid or _is_graph_node_id(bid):
        return ""
    if bid.startswith("biz:yelp:"):
        return bid.split("biz:yelp:", 1)[1].strip()
    return bid


def _business_id(row: dict[str, Any]) -> str:
    # Prefer stamped business_id / Yelp doc_key over project ``id`` (often file::).
    for key in ("business_id", "doc_key", "src_key", "source"):
        cand = _canonicalize_business_id(_first_str(row, (key,)))
        if cand:
            return cand
    # ``id`` is last: find/project commonly put graph node ids here.
    for key in ("id", "node_id"):
        cand = _canonicalize_business_id(_first_str(row, (key,)))
        if cand:
            return cand
    return ""


def _is_open_str(row: dict[str, Any]) -> str:
    for key in ("is_open", "open_now"):
        if key not in row or row[key] is None:
            continue
        val = row[key]
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return "true" if int(val) == 1 else "false"
        text = str(val).strip().lower()
        if text in {"1", "true", "yes", "open"}:
            return "true"
        if text in {"0", "false", "no", "closed"}:
            return "false"
    return ""


def _normalize_row(row: Any) -> dict[str, str] | None:
    if not isinstance(row, dict):
        return None

    # Skip pure review rows for card list (unless they carry a business name)
    et = str(row.get("entity_type") or "").lower()
    if et == "review" and not row.get("name") and not row.get("business_id"):
        return None

    row = _merge_blob_into_row(row)

    name = _first_str(row, NAME_KEYS)
    if not name or _is_json_blob_text(name):
        return None

    description = _first_str(row, DESC_KEYS)
    if _is_json_blob_text(description):
        inner = _try_parse_json_obj(description) or {}
        nested = inner.get("description") or inner.get("text")
        description = nested.strip() if isinstance(nested, str) else ""

    # Prefer short prose; avoid dumping full review text as business description
    if et == "review" and description and len(description) > 280:
        description = description[:277] + "..."

    card: dict[str, str] = {
        "name": name,
        "description": description,
        "image": _first_str(row, IMAGE_KEYS),
    }

    bid = _business_id(row)
    if bid:
        card["business_id"] = bid

    rating = _first_str(row, RATING_KEYS)
    if rating:
        card["rating"] = rating

    rc = _first_str(row, REVIEW_COUNT_KEYS)
    if rc:
        card["review_count"] = rc

    cats = _categories(row)
    if cats:
        card["categories"] = cats

    price = _price_label(row)
    if price:
        card["price"] = price

    address = _first_str(row, ("address",))
    location = _build_location(row)
    if location:
        card["location"] = location
    if address:
        card["address"] = address

    for key in ("city", "state"):
        val = _first_str(row, (key,))
        if val:
            card[key] = val

    lat = _first_str(row, LAT_KEYS)
    lon = _first_str(row, LON_KEYS)
    if lat:
        card["latitude"] = lat
    if lon:
        card["longitude"] = lon

    open_s = _is_open_str(row)
    if open_s:
        card["is_open"] = open_s

    hours = row.get("hours")
    if isinstance(hours, dict):
        # leave empty hours_today; UI can format later
        pass
    elif hours is not None:
        hs = str(hours).strip()
        if hs and hs.lower() not in {"null", "none"}:
            card["hours_today"] = hs

    url = _first_str(row, URL_KEYS)
    if url:
        card["url"] = url

    return card


def _collect_arrays(obj: Any, found: list) -> None:
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                found.append(item)
        return
    if not isinstance(obj, dict):
        return
    for key in ("rows", "items", "results", "data", "businesses", "matches", "nodes"):
        val = obj.get(key)
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    found.append(item)
    for key in ("return", "output"):
        val = obj.get(key)
        if isinstance(val, dict):
            _collect_arrays(val, found)
        elif isinstance(val, list):
            _collect_arrays(val, found)
    steps = obj.get("steps")
    if isinstance(steps, dict):
        for step_val in steps.values():
            if isinstance(step_val, dict):
                _collect_arrays(step_val, found)


def _rows_from_tool_call(rec: dict) -> list[dict]:
    rows: list[dict] = []
    parsed = rec.get("result_json")
    if isinstance(parsed, dict):
        _collect_arrays(parsed, rows)
    if rows:
        return rows
    raw = rec.get("result_text") or rec.get("result") or ""
    if not raw:
        return rows
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return rows
    _collect_arrays(data, rows)
    return rows


def zeus_data_to_results(zeus_data: list[dict] | None) -> list[dict[str, str]]:
    """Convert schema-filtered zeus_data rows into business cards."""
    from local_guide.business_images import apply_local_images

    if not zeus_data:
        return []

    seen: set[str] = set()
    results: list[dict[str, str]] = []
    for row in zeus_data:
        card = _normalize_row(row)
        if not card:
            continue
        key = (card.get("business_id") or card["name"]).lower()
        if key in seen:
            continue
        seen.add(key)
        apply_local_images(card)
        results.append(card)
        if len(results) >= MAX_RESULTS:
            break
    return results


def extract_businesses(trace: dict | None) -> list[dict[str, str]]:
    """Walk trace tool_calls and return normalized business cards."""
    from local_guide.business_images import apply_local_images

    if not trace:
        return []

    seen: set[str] = set()
    results: list[dict[str, str]] = []

    for rec in trace.get("tool_calls") or []:
        for row in _rows_from_tool_call(rec):
            card = _normalize_row(row)
            if not card:
                continue
            key = (card.get("business_id") or card["name"]).lower()
            if key in seen:
                continue
            seen.add(key)
            apply_local_images(card)
            results.append(card)
            if len(results) >= MAX_RESULTS:
                return results

    return results


# Alias used by answer_parser imports in some call sites
extract_destinations = extract_businesses
