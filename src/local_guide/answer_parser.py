"""Parse structured markdown LLM answers into JSON."""
from __future__ import annotations

import json
import re
from typing import Any

from local_guide.results_parser import MAX_RESULTS

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
_SECTION = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)
_NUMBERED_ITEM = re.compile(r"^\d+\.\s+\*\*(.+?)\*\*\s*$", re.MULTILINE)
_BULLET_FIELD = re.compile(r"^-\s+\*\*(.+?)\*\*:\s*(.+)$", re.MULTILINE)
_TIP = re.compile(r"\*\*Tip\*\*:\s*(.+?)(?=\n\n|\n\*\*|$)", re.DOTALL | re.IGNORECASE)
_FOLLOW_UP = re.compile(r"(Would you like\b.+?)\?\s*$", re.DOTALL | re.IGNORECASE)

_FIELD_ALIASES = {
    "location": "location",
    "address": "address",
    "description": "description",
    "image": "image",
    "price": "price",
    "rating": "rating",
    "stars": "rating",
    "categories": "categories",
    "category": "categories",
    "url": "url",
    "business_id": "business_id",
}


def _strip_bold(text: str) -> str:
    return _BOLD.sub(r"\1", text).strip()


def _field_key(label: str) -> str:
    normalized = label.strip().lower()
    return _FIELD_ALIASES.get(normalized, normalized.replace(" ", "_"))


def _normalize_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").strip()
    text = re.sub(r"(?<!\n)(###\s)", r"\n\1", text)
    text = re.sub(r"(?<!\n)(\d+\.\s+\*\*)", r"\n\1", text)
    text = re.sub(r"(?<!\n)(-\s+\*\*)", r"\n\1", text)
    text = re.sub(r"(?<!\n)(\*\*Tip\*\*:)", r"\n\1", text, flags=re.IGNORECASE)
    return text.strip()


def _try_parse_json_block(text: str) -> dict[str, Any] | None:
    match = _JSON_FENCE.search(text)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except (TypeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _split_section_header(header: str) -> tuple[str, str]:
    cleaned = _strip_bold(header)
    for sep in (" – ", " - ", " — "):
        if sep in cleaned:
            name, section = cleaned.split(sep, 1)
            return name.strip(), section.strip()
    return cleaned, ""


def _parse_item_block(block: str) -> dict[str, str]:
    lines = block.strip().split("\n")
    if not lines:
        return {}

    name = _strip_bold(lines[0])
    item: dict[str, str] = {"name": name}

    for line in lines[1:]:
        match = _BULLET_FIELD.match(line.strip())
        if not match:
            continue
        key = _field_key(_strip_bold(match.group(1)))
        item[key] = match.group(2).strip()

    return item


def _parse_numbered_items(body: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    matches = list(_NUMBERED_ITEM.finditer(body))
    if not matches:
        return items

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        parsed = _parse_item_block(match.group(1) + "\n" + body[start:end])
        if parsed.get("name"):
            items.append(parsed)
    return items


def _extract_context(text: str) -> str:
    first_section = _SECTION.search(text)
    intro = text[: first_section.start()] if first_section else text
    intro = _strip_bold(intro)
    intro = re.sub(r"\s+", " ", intro).strip()
    if not intro:
        return ""
    if "zeus" in intro.lower() or "unavailable" in intro.lower():
        return intro
    return intro if len(intro) > 40 else ""


def _extract_tip(text: str) -> str:
    match = _TIP.search(text)
    return match.group(1).strip() if match else ""


def _extract_follow_up(text: str) -> str:
    match = _FOLLOW_UP.search(text.strip())
    return match.group(1).strip() + "?" if match else ""


def parse_markdown_answer(text: str | None) -> dict[str, Any] | None:
    """Parse a markdown LLM answer into structured JSON.

    Returns None when no recognizable structure is found.
    """
    if isinstance(text, dict):
        return text if text else None
    if not isinstance(text, str) or not text.strip():
        return None

    embedded = _try_parse_json_block(text)
    if embedded is not None:
        return embedded

    normalized = _normalize_markdown(text)
    sections = list(_SECTION.finditer(normalized))
    if not sections:
        items = _parse_numbered_items(normalized)
        if not items:
            return None
        result: dict[str, Any] = {"items": items}
        tip = _extract_tip(normalized)
        if tip:
            result["tip"] = tip
        context = _extract_context(normalized)
        if context:
            result["context"] = context
        follow_up = _extract_follow_up(normalized)
        if follow_up:
            result["follow_up"] = follow_up
        return result

    generic_sections: list[dict[str, Any]] = []

    for index, match in enumerate(sections):
        start = match.end()
        end = sections[index + 1].start() if index + 1 < len(sections) else len(normalized)
        header = match.group(1).strip()
        body = normalized[start:end]
        name, section_label = _split_section_header(header)
        items = _parse_numbered_items(body)

        entry: dict[str, Any] = {"name": name}
        if section_label:
            entry["section"] = section_label
        if items:
            entry["items"] = items
            generic_sections.append(entry)

    if not generic_sections:
        # Still try whole-doc numbered list
        items = _parse_numbered_items(normalized)
        if not items:
            return None
        result = {"items": items}
    else:
        result = {"sections": generic_sections}

    tip = _extract_tip(normalized)
    if tip:
        result["tip"] = tip
    context = _extract_context(normalized)
    if context:
        result["context"] = context
    follow_up = _extract_follow_up(normalized)
    if follow_up:
        result["follow_up"] = follow_up

    return result


def structured_answer_to_results(data: dict[str, Any] | None) -> list[dict[str, str]]:
    """Flatten structured answer JSON into business-style result cards."""
    if not data:
        return []

    results: list[dict[str, str]] = []
    seen: set[str] = set()

    def add_card(item: dict[str, Any], fallback_location: str = "") -> None:
        name = str(item.get("name") or "").strip()
        key = name.lower()
        if not name or key in seen:
            return
        seen.add(key)
        location = (
            str(item.get("location") or "").strip()
            or str(item.get("address") or "").strip()
            or fallback_location
        )
        image = str(item.get("image") or item.get("image_url") or "").strip()
        card: dict[str, str] = {
            "name": name,
            "description": str(item.get("description") or ""),
            "image": image,
        }
        if location:
            card["location"] = location
        price = str(item.get("price") or "").strip()
        if price:
            card["price"] = price
        rating = str(item.get("rating") or item.get("stars") or "").strip()
        if rating:
            card["rating"] = rating
        cats = str(item.get("categories") or item.get("category") or "").strip()
        if cats:
            card["categories"] = cats
        bid = str(item.get("business_id") or item.get("id") or "").strip()
        if bid:
            card["business_id"] = bid
        url = str(item.get("url") or "").strip()
        if url:
            card["url"] = url
        results.append(card)

    for section in data.get("sections") or []:
        section_name = str(section.get("name") or "").rstrip(":").strip()
        fallback = (
            ""
            if section_name.lower()
            in {"top matching businesses", "businesses", "results", "recommendations"}
            else section_name
        )
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            add_card(item, fallback)

    # Travel-style airports.hotels still map if model emits them
    for airport in data.get("airports") or []:
        airport_name = str(airport.get("name") or "")
        for hotel in airport.get("hotels") or []:
            if isinstance(hotel, dict):
                add_card(hotel, airport_name)

    for item in data.get("items") or []:
        if isinstance(item, dict):
            add_card(item)

    for item in data.get("businesses") or []:
        if isinstance(item, dict):
            add_card(item)

    return results[:MAX_RESULTS]
