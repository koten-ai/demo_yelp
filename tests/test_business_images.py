"""Unit tests for local business image catalog overlay."""
from __future__ import annotations

import json
from pathlib import Path

from local_guide import business_images as bi
from local_guide.results_parser import zeus_data_to_results


def test_apply_local_images_from_disk(tmp_path, monkeypatch):
    root = tmp_path / "business-images"
    bid = "biz:TEST123"
    d = root / bid
    d.mkdir(parents=True)
    (d / "1.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    (d / "2.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"1" * 64)
    (d / "3.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"2" * 64)

    monkeypatch.setattr(bi, "IMAGES_ROOT", root)
    monkeypatch.setattr(bi, "MANIFEST_PATH", root / "manifest.json")
    bi.load_catalog(force=True)

    card = {"name": "Test Cafe", "business_id": bid, "image": "", "description": ""}
    bi.apply_local_images(card)
    assert card["image"] == f"/business-images/{bid}/1.png"
    assert card["images"] == [
        f"/business-images/{bid}/1.png",
        f"/business-images/{bid}/2.png",
        f"/business-images/{bid}/3.png",
    ]


def test_zeus_data_to_results_attaches_images(tmp_path, monkeypatch):
    root = tmp_path / "business-images"
    bid = "biz:ABC"
    d = root / bid
    d.mkdir(parents=True)
    (d / "1.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    monkeypatch.setattr(bi, "IMAGES_ROOT", root)
    monkeypatch.setattr(bi, "MANIFEST_PATH", root / "manifest.json")
    bi.load_catalog(force=True)

    cards = zeus_data_to_results(
        [
            {
                "entity_type": "Business",
                "business_id": bid,
                "name": "Alpha",
                "stars": 5,
                "city": "Philly",
            }
        ]
    )
    assert cards[0]["image"].endswith("/1.png")
    assert "images" in cards[0]


def test_write_manifest_roundtrip(tmp_path, monkeypatch):
    root = tmp_path / "business-images"
    root.mkdir()
    monkeypatch.setattr(bi, "IMAGES_ROOT", root)
    monkeypatch.setattr(bi, "MANIFEST_PATH", root / "manifest.json")
    path = bi.write_manifest(
        {
            "biz:X": {
                "name": "X",
                "image": "1.png",
                "images": ["1.png", "2.png", "3.png"],
            }
        }
    )
    assert path.is_file()
    data = json.loads(path.read_text())
    assert "biz:X" in data["businesses"]
    cat = bi.load_catalog(force=True)
    assert cat["biz:X"][0].startswith("/business-images/biz:X/")


def test_business_images_base_url_env(tmp_path, monkeypatch):
    root = tmp_path / "business-images"
    bid = "biz:CDN1"
    d = root / bid
    d.mkdir(parents=True)
    (d / "1.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    (d / "2.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"1" * 64)

    base = "https://koten-yelp-demo-photos.nyc3.cdn.digitaloceanspaces.com/business-images"
    monkeypatch.setenv("BUSINESS_IMAGES_BASE_URL", base)
    monkeypatch.setattr(bi, "IMAGES_ROOT", root)
    monkeypatch.setattr(bi, "MANIFEST_PATH", root / "manifest.json")
    bi.load_catalog(force=True)

    assert bi.get_url_prefix() == base
    assert bi.public_image_url(bid, "1.png") == f"{base}/{bid}/1.png"

    card = {"name": "CDN Cafe", "business_id": bid, "image": ""}
    bi.apply_local_images(card)
    assert card["image"] == f"{base}/{bid}/1.png"
    assert card["images"] == [
        f"{base}/{bid}/1.png",
        f"{base}/{bid}/2.png",
    ]

    # Relative paths in manifest re-home under CDN base
    bi.write_manifest(
        {
            bid: {
                "business_id": bid,
                "image": f"/business-images/{bid}/1.png",
                "images": [
                    f"/business-images/{bid}/1.png",
                    f"/business-images/{bid}/2.png",
                ],
            }
        }
    )
    cat = bi.load_catalog(force=True)
    assert cat[bid][0] == f"{base}/{bid}/1.png"
    data = json.loads((root / "manifest.json").read_text())
    assert data["url_prefix"] == base


def test_business_images_base_url_trailing_slash(monkeypatch):
    monkeypatch.setenv(
        "BUSINESS_IMAGES_BASE_URL",
        "https://example.cdn.digitaloceanspaces.com/business-images/",
    )
    assert bi.get_url_prefix() == "https://example.cdn.digitaloceanspaces.com/business-images"
    assert (
        bi.public_image_url("biz:A", "3.png")
        == "https://example.cdn.digitaloceanspaces.com/business-images/biz:A/3.png"
    )
