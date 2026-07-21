#!/usr/bin/env python3
"""
Add a key/value pair to every object in a JSON file.

Supports:
  - JSON Lines (JSONL / NDJSON): one JSON object per line (Yelp dataset style)
  - JSON array: [ {...}, {...}, ... ]
  - Single JSON object: { ... }

Examples:
  # Add type=User to every line, write to a new file
  python add_json_field.py yelp_academic_dataset_user.json -k type -v User -o users_with_type.json

  # In-place update (writes to a temp file, then replaces the original)
  python add_json_field.py data.json -k type -v User --in-place

  # Numeric / JSON values
  python add_json_field.py data.json -k active -v true --value-type bool
  python add_json_field.py data.json -k score -v 10 --value-type int
  python add_json_field.py data.json -k meta -v '{"source":"yelp"}' --value-type json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator, TextIO


def parse_value(raw: str, value_type: str) -> Any:
    """Convert CLI string to the requested Python/JSON type."""
    if value_type == "str":
        return raw
    if value_type == "int":
        return int(raw)
    if value_type == "float":
        return float(raw)
    if value_type == "bool":
        lowered = raw.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
        raise ValueError(f"Cannot parse bool from: {raw!r}")
    if value_type == "null":
        return None
    if value_type == "json":
        return json.loads(raw)
    raise ValueError(f"Unknown value type: {value_type}")


def detect_format(path: Path, max_lines: int = 20) -> str:
    """
    Detect whether file is JSONL, a JSON array, or a single object.
    Returns: 'jsonl' | 'array' | 'object'

    Yelp-style JSONL can have very long lines (hundreds of KB per record), so
    detection reads full lines rather than a fixed byte sample.
    """
    with path.open("r", encoding="utf-8") as f:
        # Skip leading blank lines / BOM
        first_line = ""
        while True:
            line = f.readline()
            if not line:
                return "jsonl"
            # Strip BOM from the very first non-empty content
            s = line.lstrip("\ufeff").strip()
            if not s:
                continue
            first_line = s
            break

        if first_line.startswith("["):
            return "array"
        if not first_line.startswith("{"):
            # Fallback: assume JSONL if first non-ws isn't [ or {
            return "jsonl"

        # Starts with '{': could be one object or JSONL (one object per line).
        # Count subsequent non-empty lines that also look like objects.
        # Important: do NOT use a small byte sample — first records can be huge.
        non_empty = 1
        starts_with_brace = 1
        for _ in range(max_lines - 1):
            line = f.readline()
            if not line:
                break
            s = line.strip()
            if not s:
                continue
            non_empty += 1
            if s.startswith("{"):
                starts_with_brace += 1

        if non_empty >= 2 and starts_with_brace == non_empty:
            return "jsonl"
        return "object"


def add_field(obj: dict, key: str, value: Any, overwrite: bool) -> dict:
    if not isinstance(obj, dict):
        raise TypeError(f"Expected object/dict, got {type(obj).__name__}")
    if key in obj and not overwrite:
        return obj
    obj[key] = value
    return obj


def process_jsonl(
    infile: TextIO,
    outfile: TextIO,
    key: str,
    value: Any,
    overwrite: bool,
    progress_every: int,
) -> int:
    count = 0
    for line_no, line in enumerate(infile, start=1):
        stripped = line.strip()
        if not stripped:
            outfile.write(line)
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as e:
            raise SystemExit(f"Invalid JSON on line {line_no}: {e}") from e
        add_field(obj, key, value, overwrite)
        outfile.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
        outfile.write("\n")
        count += 1
        if progress_every and count % progress_every == 0:
            print(f"  processed {count:,} records...", file=sys.stderr)
    return count


def process_array(
    infile: TextIO,
    outfile: TextIO,
    key: str,
    value: Any,
    overwrite: bool,
    progress_every: int,
    indent: int | None,
) -> int:
    data = json.load(infile)
    if not isinstance(data, list):
        raise SystemExit("Expected a JSON array at top level")
    for i, item in enumerate(data, start=1):
        add_field(item, key, value, overwrite)
        if progress_every and i % progress_every == 0:
            print(f"  processed {i:,} records...", file=sys.stderr)
    json.dump(data, outfile, ensure_ascii=False, indent=indent)
    if indent is not None:
        outfile.write("\n")
    return len(data)


def process_object(
    infile: TextIO,
    outfile: TextIO,
    key: str,
    value: Any,
    overwrite: bool,
    indent: int | None,
) -> int:
    data = json.load(infile)
    if not isinstance(data, dict):
        raise SystemExit("Expected a JSON object at top level")
    add_field(data, key, value, overwrite)
    json.dump(data, outfile, ensure_ascii=False, indent=indent)
    if indent is not None:
        outfile.write("\n")
    return 1


def open_output(
    in_path: Path,
    out_path: Path | None,
    in_place: bool,
) -> tuple[TextIO, Path | None, bool]:
    """
    Returns (outfile, temp_path_or_None, should_replace_input).
    temp_path is set when we need to rename over the destination at the end.
    """
    if in_place:
        # Write to temp in same directory so os.replace is atomic on same filesystem
        fd, tmp = tempfile.mkstemp(
            prefix=in_path.name + ".",
            suffix=".tmp",
            dir=in_path.parent,
            text=True,
        )
        return os.fdopen(fd, "w", encoding="utf-8"), Path(tmp), True

    if out_path is None:
        raise SystemExit("Provide -o/--output or use --in-place")

    if out_path.resolve() == in_path.resolve():
        # Same path without --in-place: treat as in-place for safety
        fd, tmp = tempfile.mkstemp(
            prefix=in_path.name + ".",
            suffix=".tmp",
            dir=in_path.parent,
            text=True,
        )
        return os.fdopen(fd, "w", encoding="utf-8"), Path(tmp), True

    out_path.parent.mkdir(parents=True, exist_ok=True)
    return out_path.open("w", encoding="utf-8"), None, False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Add a key/value pair to every item in a JSON/JSONL file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", type=Path, help="Input JSON or JSONL file")
    parser.add_argument(
        "-k",
        "--key",
        required=True,
        help="Key to add (e.g. type)",
    )
    parser.add_argument(
        "-v",
        "--value",
        required=True,
        help="Value to set (string by default; see --value-type)",
    )
    parser.add_argument(
        "--value-type",
        choices=("str", "int", "float", "bool", "null", "json"),
        default="str",
        help="How to interpret --value (default: str)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file path",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Update the input file in place (via temp file + atomic replace)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the key if it already exists (default: leave existing)",
    )
    parser.add_argument(
        "--format",
        choices=("auto", "jsonl", "array", "object"),
        default="auto",
        help="Input format (default: auto-detect)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="Pretty-print indent for array/object output (JSONL stays one line per record)",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=100_000,
        help="Print progress every N records (0 disables; default: 100000)",
    )
    args = parser.parse_args(argv)

    in_path: Path = args.input
    if not in_path.is_file():
        print(f"Error: input file not found: {in_path}", file=sys.stderr)
        return 1

    if not args.in_place and args.output is None:
        print("Error: specify -o/--output or --in-place", file=sys.stderr)
        return 1

    try:
        value = parse_value(args.value, args.value_type)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error parsing value: {e}", file=sys.stderr)
        return 1

    fmt = args.format
    if fmt == "auto":
        fmt = detect_format(in_path)
        print(f"Detected format: {fmt}", file=sys.stderr)

    outfile, tmp_path, replace_input = open_output(in_path, args.output, args.in_place)
    dest_for_replace = in_path if args.in_place or replace_input else args.output

    try:
        with in_path.open("r", encoding="utf-8") as infile, outfile:
            if fmt == "jsonl":
                n = process_jsonl(
                    infile,
                    outfile,
                    args.key,
                    value,
                    args.overwrite,
                    args.progress_every,
                )
            elif fmt == "array":
                n = process_array(
                    infile,
                    outfile,
                    args.key,
                    value,
                    args.overwrite,
                    args.progress_every,
                    args.indent,
                )
            else:
                n = process_object(
                    infile,
                    outfile,
                    args.key,
                    value,
                    args.overwrite,
                    args.indent,
                )
            outfile.flush()
            os.fsync(outfile.fileno())

        if tmp_path is not None:
            os.replace(tmp_path, dest_for_replace)
            tmp_path = None

    except Exception:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise

    out_desc = str(in_path) if args.in_place else str(args.output or in_path)
    print(
        f"Done. Added {args.key!r}={value!r} to {n:,} record(s) → {out_desc}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
