#!/usr/bin/env python3
"""Validate structural invariants for editable legal-process SVG files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


SVG_NS = "{http://www.w3.org/2000/svg}"


def svg_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.rglob("*.svg"))


def validate(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        return [f"invalid XML: {exc}"], warnings

    if root.tag != f"{SVG_NS}svg":
        errors.append("root element is not an SVG element in the SVG namespace")
    if not root.get("viewBox"):
        errors.append("missing viewBox")

    title = root.find(f"{SVG_NS}title")
    desc = root.find(f"{SVG_NS}desc")
    if title is None or not "".join(title.itertext()).strip():
        errors.append("missing non-empty <title>")
    if desc is None or not "".join(desc.itertext()).strip():
        errors.append("missing non-empty <desc>")

    ids: set[str] = set()
    for element in root.iter():
        element_id = element.get("id")
        if element_id:
            if element_id in ids:
                errors.append(f"duplicate id: {element_id}")
            ids.add(element_id)

    text_elements = list(root.iter(f"{SVG_NS}text"))
    if not text_elements:
        errors.append("no editable <text> elements found")

    for image in root.iter(f"{SVG_NS}image"):
        href = image.get("href") or image.get("{http://www.w3.org/1999/xlink}href") or ""
        if href.startswith(("http://", "https://")):
            warnings.append(f"external raster/image reference: {href}")
        else:
            warnings.append("embedded or linked <image> reduces pure-vector editability")

    groups = [g for g in root.iter(f"{SVG_NS}g") if g.get("id")]
    if not groups:
        warnings.append("no grouped elements with descriptive ids")

    source_text = " ".join("".join(t.itertext()) for t in text_elements)
    if "§" not in source_text and "Rule" not in source_text and "Article" not in source_text and "依据" not in source_text:
        warnings.append("no visible authority marker found; confirm whether citations are required")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="SVG file or directory containing SVG files")
    args = parser.parse_args()

    files = svg_files(args.target)
    if not files:
        print(f"ERROR: no SVG files found under {args.target}", file=sys.stderr)
        return 2

    failed = False
    for path in files:
        errors, warnings = validate(path)
        status = "FAIL" if errors else "OK"
        print(f"{status}: {path}")
        for message in errors:
            print(f"  ERROR: {message}")
        for message in warnings:
            print(f"  WARN: {message}")
        failed = failed or bool(errors)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
