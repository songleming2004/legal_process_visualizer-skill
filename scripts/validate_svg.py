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


@dataclass(frozen=True)
class PathGeometry:
    points: list[tuple[float, float]]
    start_delta: tuple[float, float]
    end_delta: tuple[float, float]
    curved: bool


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


def cubic_point(
    start: tuple[float, float], control_1: tuple[float, float],
    control_2: tuple[float, float], end: tuple[float, float], t: float
) -> tuple[float, float]:
    inverse = 1.0 - t
    x = (
        inverse ** 3 * start[0]
        + 3 * inverse ** 2 * t * control_1[0]
        + 3 * inverse * t ** 2 * control_2[0]
        + t ** 3 * end[0]
    )
    y = (
        inverse ** 3 * start[1]
        + 3 * inverse ** 2 * t * control_1[1]
        + 3 * inverse * t ** 2 * control_2[1]
        + t ** 3 * end[1]
    )
    return x, y


def parse_connector_path(path_data: str, curve_samples: int = 32) -> PathGeometry:
    tokens = PATH_TOKEN.findall(path_data.replace(",", " "))
    if not tokens:
        raise ValueError("empty path data")

    points: list[tuple[float, float]] = []
    current = (0.0, 0.0)
    subpath_start = current
    command: str | None = None
    previous_cubic_control: tuple[float, float] | None = None
    start_delta: tuple[float, float] | None = None
    end_delta: tuple[float, float] | None = None
    curved = False
    i = 0

    def require_numbers(count: int) -> None:
        if i + count > len(tokens) or any(token.isalpha() for token in tokens[i:i + count]):
            raise ValueError(f"command {command} requires {count} numeric values")

    def add_line(end: tuple[float, float]) -> None:
        nonlocal current, start_delta, end_delta, previous_cubic_control
        delta = movement(current, end)
        if delta == (0.0, 0.0):
            raise ValueError("zero-length connector segment")
        if start_delta is None:
            start_delta = delta
        end_delta = delta
        points.append(end)
        current = end
        previous_cubic_control = None

    def add_cubic(
        control_1: tuple[float, float], control_2: tuple[float, float], end: tuple[float, float]
    ) -> None:
        nonlocal current, start_delta, end_delta, previous_cubic_control, curved
        sampled = [cubic_point(current, control_1, control_2, end, step / curve_samples)
                   for step in range(1, curve_samples + 1)]
        first_tangent = movement(current, control_1)
        if first_tangent == (0.0, 0.0):
            first_tangent = movement(current, sampled[0])
        final_tangent = movement(control_2, end)
        if final_tangent == (0.0, 0.0):
            final_tangent = movement(sampled[-2], end)
        if first_tangent == (0.0, 0.0) or final_tangent == (0.0, 0.0):
            raise ValueError("cubic connector has an undefined endpoint tangent")
        if start_delta is None:
            start_delta = first_tangent
        end_delta = final_tangent
        points.extend(sampled)
        current = end
        previous_cubic_control = control_2
        curved = True

    while i < len(tokens):
        token = tokens[i]
        if token.isalpha():
            command = token
            i += 1
            if command.islower():
                raise ValueError(f"relative command {command} is not supported")
            if command not in {"M", "L", "H", "V", "C", "S", "Z"}:
                raise ValueError(f"path command {command} is not supported")
            if command == "Z":
                add_line(subpath_start)
                command = None
            continue
        if command is None:
            raise ValueError("number without an active path command")

        if command in {"M", "L"}:
            require_numbers(2)
            end = (float(tokens[i]), float(tokens[i + 1]))
            if command == "M":
                current = end
                subpath_start = current
                points.append(current)
                command = "L"
                previous_cubic_control = None
            else:
                add_line(end)
            i += 2
        elif command == "H":
            require_numbers(1)
            add_line((float(tokens[i]), current[1]))
            i += 1
        elif command == "V":
            require_numbers(1)
            add_line((current[0], float(tokens[i])))
            i += 1
        elif command == "C":
            require_numbers(6)
            add_cubic(
                (float(tokens[i]), float(tokens[i + 1])),
                (float(tokens[i + 2]), float(tokens[i + 3])),
                (float(tokens[i + 4]), float(tokens[i + 5])),
            )
            i += 6
        elif command == "S":
            require_numbers(4)
            control_1 = current if previous_cubic_control is None else (
                2 * current[0] - previous_cubic_control[0],
                2 * current[1] - previous_cubic_control[1],
            )
            add_cubic(
                control_1,
                (float(tokens[i]), float(tokens[i + 1])),
                (float(tokens[i + 2]), float(tokens[i + 3])),
            )
            i += 4

    if len(points) < 2 or start_delta is None or end_delta is None:
        raise ValueError("connector path must contain at least two points")
    return PathGeometry(points, start_delta, end_delta, curved)


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
    axis_tolerance = 1e-6
    return {
        "top": dy < 0 and abs(dx) <= axis_tolerance,
        "right": dx > 0 and abs(dy) <= axis_tolerance,
        "bottom": dy > 0 and abs(dx) <= axis_tolerance,
        "left": dx < 0 and abs(dy) <= axis_tolerance,
    }[side]


def approaches_inward(delta: tuple[float, float], side: str) -> bool:
    dx, dy = delta
    axis_tolerance = 1e-6
    return {
        "top": dy > 0 and abs(dx) <= axis_tolerance,
        "right": dx < 0 and abs(dy) <= axis_tolerance,
        "bottom": dy < 0 and abs(dx) <= axis_tolerance,
        "left": dx > 0 and abs(dy) <= axis_tolerance,
    }[side]


def segment_crosses_interior(
    start: tuple[float, float], end: tuple[float, float], rect: Rect, tol: float = TOLERANCE
) -> bool:
    x1, y1 = start
    x2, y2 = end
    left, right = rect.x + tol, rect.right - tol
    top, bottom = rect.y + tol, rect.bottom - tol
    if left >= right or top >= bottom:
        return False
    dx, dy = x2 - x1, y2 - y1
    lower, upper = 0.0, 1.0
    for p, q in ((-dx, x1 - left), (dx, right - x1), (-dy, y1 - top), (dy, bottom - y1)):
        if abs(p) <= 1e-12:
            if q < 0:
                return False
            continue
        ratio = q / p
        if p < 0:
            lower = max(lower, ratio)
        else:
            upper = min(upper, ratio)
        if lower > upper:
            return False
    return upper > 0.0 and lower < 1.0 and lower <= upper


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


def inside_canvas(point: tuple[float, float], canvas: Rect, tol: float = TOLERANCE) -> bool:
    return (
        canvas.x - tol <= point[0] <= canvas.right + tol
        and canvas.y - tol <= point[1] <= canvas.bottom + tol
    )


def validate_connectors(root: ET.Element, nodes: dict[str, Rect], canvas: Rect | None) -> list[str]:
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
            geometry = parse_connector_path(path.get("d") or "")
        except ValueError as exc:
            errors.append(f"{edge_id}: {exc}")
            continue

        points = geometry.points
        source_rect = nodes[source_id]
        target_rect = nodes[target_id]
        if not on_side(points[0], source_rect, source_side):
            errors.append(f"{edge_id}: start point is detached from {source_id}.{source_side}")
        if not on_side(points[-1], target_rect, target_side):
            errors.append(f"{edge_id}: end point is detached from {target_id}.{target_side}")

        if not departs_outward(geometry.start_delta, source_side):
            errors.append(f"{edge_id}: first segment does not leave {source_id}.{source_side} outward")
        if not approaches_inward(geometry.end_delta, target_side):
            errors.append(f"{edge_id}: final segment does not approach {target_id}.{target_side} inward")

        if canvas is not None and any(not inside_canvas(point, canvas) for point in points):
            errors.append(f"{edge_id}: connector extends outside the SVG viewBox")

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
    canvas: Rect | None = None
    raw_viewbox = root.get("viewBox")
    if not raw_viewbox:
        errors.append("missing viewBox")
    else:
        try:
            values = [float(value) for value in raw_viewbox.replace(",", " ").split()]
            if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
                raise ValueError
            canvas = Rect(*values)
        except ValueError:
            errors.append(f"invalid viewBox: {raw_viewbox!r}")

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
    errors.extend(validate_connectors(root, nodes, canvas))
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
