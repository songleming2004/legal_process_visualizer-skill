#!/usr/bin/env python3
"""Validate structure and connector integrity for editable legal-process SVGs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


SVG_NS = "{http://www.w3.org/2000/svg}"
SIDE_NAMES = {"top", "right", "bottom", "left"}
NUMBER = r"-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
PATH_TOKEN = re.compile(rf"[A-Za-z]|{NUMBER}")
TOLERANCE = 1.0


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height


def svg_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.rglob("*.svg"))


def number(element: ET.Element, name: str) -> float:
    raw = element.get(name)
    if raw is None or not re.fullmatch(NUMBER, raw.strip()):
        raise ValueError(f"non-numeric or missing {name}={raw!r}")
    return float(raw)


def node_rectangles(root: ET.Element) -> tuple[dict[str, Rect], list[str]]:
    nodes: dict[str, Rect] = {}
    warnings: list[str] = []
    for group in root.iter(f"{SVG_NS}g"):
        node_id = group.get("id")
        if not node_id:
            continue
        rect = group.find(f"{SVG_NS}rect")
        if rect is None:
            continue
        if group.get("transform") or rect.get("transform"):
            warnings.append(f"node {node_id}: transforms prevent deterministic boundary validation")
            continue
        try:
            nodes[node_id] = Rect(
                number(rect, "x"), number(rect, "y"),
                number(rect, "width"), number(rect, "height")
            )
        except ValueError as exc:
            warnings.append(f"node {node_id}: {exc}")
    return nodes, warnings


def parse_orthogonal_path(path_data: str) -> list[tuple[float, float]]:
    tokens = PATH_TOKEN.findall(path_data.replace(",", " "))
    if not tokens:
        raise ValueError("empty path data")

    points: list[tuple[float, float]] = []
    current = (0.0, 0.0)
    subpath_start = current
    command: str | None = None
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.isalpha():
            command = token
            i += 1
            if command.islower():
                raise ValueError(f"relative command {command} is not supported")
            if command not in {"M", "L", "H", "V", "Z"}:
                raise ValueError(f"path command {command} is not supported")
            if command == "Z":
                current = subpath_start
                points.append(current)
                command = None
            continue
        if command is None:
            raise ValueError("number without an active path command")

        if command in {"M", "L"}:
            if i + 1 >= len(tokens) or tokens[i + 1].isalpha():
                raise ValueError(f"command {command} requires an x/y pair")
            current = (float(tokens[i]), float(tokens[i + 1]))
            points.append(current)
            if command == "M":
                subpath_start = current
                command = "L"
            i += 2
        elif command == "H":
            current = (float(tokens[i]), current[1])
            points.append(current)
            i += 1
        elif command == "V":
            current = (current[0], float(tokens[i]))
            points.append(current)
            i += 1

    if len(points) < 2:
        raise ValueError("connector path must contain at least two points")
    for start, end in zip(points, points[1:]):
        if start[0] != end[0] and start[1] != end[1]:
            raise ValueError("diagonal connector segment is not supported")
    return points


def on_side(point: tuple[float, float], rect: Rect, side: str, tol: float = TOLERANCE) -> bool:
    x, y = point
    if side == "top":
        return abs(y - rect.y) <= tol and rect.x - tol <= x <= rect.right + tol
    if side == "right":
        return abs(x - rect.right) <= tol and rect.y - tol <= y <= rect.bottom + tol
    if side == "bottom":
        return abs(y - rect.bottom) <= tol and rect.x - tol <= x <= rect.right + tol
    return abs(x - rect.x) <= tol and rect.y - tol <= y <= rect.bottom + tol


def movement(start: tuple[float, float], end: tuple[float, float]) -> tuple[float, float]:
    return end[0] - start[0], end[1] - start[1]


def departs_outward(delta: tuple[float, float], side: str) -> bool:
    dx, dy = delta
    return {
        "top": dy < 0 and dx == 0,
        "right": dx > 0 and dy == 0,
        "bottom": dy > 0 and dx == 0,
        "left": dx < 0 and dy == 0,
    }[side]


def approaches_inward(delta: tuple[float, float], side: str) -> bool:
    dx, dy = delta
    return {
        "top": dy > 0 and dx == 0,
        "right": dx < 0 and dy == 0,
        "bottom": dy < 0 and dx == 0,
        "left": dx > 0 and dy == 0,
    }[side]


def segment_crosses_interior(
    start: tuple[float, float], end: tuple[float, float], rect: Rect, tol: float = TOLERANCE
) -> bool:
    x1, y1 = start
    x2, y2 = end
    if x1 == x2:
        low, high = sorted((y1, y2))
        return rect.x + tol < x1 < rect.right - tol and max(low, rect.y + tol) < min(high, rect.bottom - tol)
    if y1 == y2:
        low, high = sorted((x1, x2))
        return rect.y + tol < y1 < rect.bottom - tol and max(low, rect.x + tol) < min(high, rect.right - tol)
    return True


def boundary_crosses_node(boundary: Rect, node: Rect) -> bool:
    sides = [
        ((boundary.x, boundary.y), (boundary.right, boundary.y)),
        ((boundary.right, boundary.y), (boundary.right, boundary.bottom)),
        ((boundary.right, boundary.bottom), (boundary.x, boundary.bottom)),
        ((boundary.x, boundary.bottom), (boundary.x, boundary.y)),
    ]
    return any(segment_crosses_interior(a, b, node, 0.0) for a, b in sides)


def is_arrowed_path(path: ET.Element) -> bool:
    classes = set((path.get("class") or "").split())
    return bool(path.get("marker-end") or classes.intersection({"connector", "conditional"}))


def validate_connectors(root: ET.Element, nodes: dict[str, Rect]) -> list[str]:
    errors: list[str] = []
    for index, path in enumerate(root.iter(f"{SVG_NS}path"), start=1):
        arrowed = is_arrowed_path(path)
        has_contract = bool(path.get("data-from") or path.get("data-to"))
        if not arrowed and not has_contract:
            continue

        edge_id = path.get("id") or f"path#{index}"
        source_id = path.get("data-from")
        target_id = path.get("data-to")
        source_side = path.get("data-from-side")
        target_side = path.get("data-to-side")

        if arrowed and (not source_id or not target_id):
            errors.append(f"{edge_id}: arrowed connector missing data-from or data-to")
            continue
        if not source_id or not target_id:
            errors.append(f"{edge_id}: partial connector contract")
            continue
        if source_side not in SIDE_NAMES or target_side not in SIDE_NAMES:
            errors.append(f"{edge_id}: sides must be one of {sorted(SIDE_NAMES)}")
            continue
        if source_id not in nodes:
            errors.append(f"{edge_id}: source node {source_id!r} has no untransformed rect")
            continue
        if target_id not in nodes:
            errors.append(f"{edge_id}: target node {target_id!r} has no untransformed rect")
            continue

        try:
            points = parse_orthogonal_path(path.get("d") or "")
        except ValueError as exc:
            errors.append(f"{edge_id}: {exc}")
            continue

        source_rect = nodes[source_id]
        target_rect = nodes[target_id]
        if not on_side(points[0], source_rect, source_side):
            errors.append(f"{edge_id}: start point is detached from {source_id}.{source_side}")
        if not on_side(points[-1], target_rect, target_side):
            errors.append(f"{edge_id}: end point is detached from {target_id}.{target_side}")

        first_delta = movement(points[0], points[1])
        last_delta = movement(points[-2], points[-1])
        if not departs_outward(first_delta, source_side):
            errors.append(f"{edge_id}: first segment does not leave {source_id}.{source_side} outward")
        if not approaches_inward(last_delta, target_side):
            errors.append(f"{edge_id}: final segment does not approach {target_id}.{target_side} inward")

        for node_id, rect in nodes.items():
            if node_id in {source_id, target_id}:
                continue
            if any(segment_crosses_interior(a, b, rect) for a, b in zip(points, points[1:])):
                errors.append(f"{edge_id}: connector crosses unrelated node {node_id}")
    return errors


def validate_boundaries(root: ET.Element, nodes: dict[str, Rect]) -> list[str]:
    errors: list[str] = []
    for index, rect_element in enumerate(root.iter(f"{SVG_NS}rect"), start=1):
        classes = set((rect_element.get("class") or "").split())
        if not classes.intersection({"boundary", "moduleBoundary", "module-boundary"}):
            continue
        boundary_id = rect_element.get("id") or f"boundary-rect#{index}"
        try:
            boundary = Rect(
                number(rect_element, "x"), number(rect_element, "y"),
                number(rect_element, "width"), number(rect_element, "height")
            )
        except ValueError as exc:
            errors.append(f"{boundary_id}: {exc}")
            continue
        for node_id, node in nodes.items():
            if boundary_crosses_node(boundary, node):
                errors.append(f"{boundary_id}: module boundary crosses node {node_id}")
    return errors


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

    nodes, node_warnings = node_rectangles(root)
    warnings.extend(node_warnings)
    errors.extend(validate_connectors(root, nodes))
    errors.extend(validate_boundaries(root, nodes))
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
