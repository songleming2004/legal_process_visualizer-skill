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
VISUAL_SEPARATION = 24.0
MIN_SHARED_LENGTH = 32.0
MAX_SHARED_RATIO = 0.35


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


@dataclass(frozen=True)
class ConnectorRecord:
    edge_id: str
    source_id: str
    target_id: str
    source_side: str
    target_side: str
    arrowed: bool
    classes: frozenset[str]
    geometry: PathGeometry


def svg_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.rglob("*.svg"))


def number(element: ET.Element, name: str) -> float:
    raw = element.get(name)
    if raw is None or not re.fullmatch(NUMBER, raw.strip()):
        raise ValueError(f"non-numeric or missing {name}={raw!r}")
    return float(raw)


def polygon_points(element: ET.Element) -> list[tuple[float, float]]:
    raw = element.get("points") or ""
    values = re.findall(NUMBER, raw)
    if len(values) != 8:
        raise ValueError("decision polygon must contain exactly four coordinate pairs")
    return [(float(values[index]), float(values[index + 1])) for index in range(0, 8, 2)]


def node_geometries(root: ET.Element) -> tuple[dict[str, Rect], dict[str, str], list[str]]:
    nodes: dict[str, Rect] = {}
    node_shapes: dict[str, str] = {}
    warnings: list[str] = []
    for group in root.iter(f"{SVG_NS}g"):
        node_id = group.get("id")
        if not node_id:
            continue
        if group.get("data-node-shape") == "decision":
            polygon = group.find(f"{SVG_NS}polygon")
            if polygon is None:
                warnings.append(f"node {node_id}: decision node has no polygon")
                continue
            if group.get("transform") or polygon.get("transform"):
                warnings.append(f"node {node_id}: transforms prevent deterministic boundary validation")
                continue
            try:
                points = polygon_points(polygon)
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                bounds = Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
                expected = {
                    (bounds.x + bounds.width / 2, bounds.y),
                    (bounds.right, bounds.y + bounds.height / 2),
                    (bounds.x + bounds.width / 2, bounds.bottom),
                    (bounds.x, bounds.y + bounds.height / 2),
                }
                if bounds.width <= 0 or bounds.height <= 0 or set(points) != expected:
                    raise ValueError(
                        "decision polygon vertices must be the top, right, bottom, and left midpoints"
                    )
                nodes[node_id] = bounds
                node_shapes[node_id] = "decision"
            except ValueError as exc:
                warnings.append(f"node {node_id}: {exc}")
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
            node_shapes[node_id] = "rect"
        except ValueError as exc:
            warnings.append(f"node {node_id}: {exc}")
    return nodes, node_shapes, warnings


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


def on_side(
    point: tuple[float, float], rect: Rect, side: str,
    shape: str = "rect", tol: float = TOLERANCE
) -> bool:
    x, y = point
    if shape == "decision":
        vertices = {
            "top": (rect.x + rect.width / 2, rect.y),
            "right": (rect.right, rect.y + rect.height / 2),
            "bottom": (rect.x + rect.width / 2, rect.bottom),
            "left": (rect.x, rect.y + rect.height / 2),
        }
        return point_distance(point, vertices[side]) <= tol
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


def point_inside_diamond(point: tuple[float, float], bounds: Rect, tol: float = TOLERANCE) -> bool:
    half_width = bounds.width / 2
    half_height = bounds.height / 2
    if half_width <= tol or half_height <= tol:
        return False
    center_x = bounds.x + half_width
    center_y = bounds.y + half_height
    return (
        abs(point[0] - center_x) / (half_width - tol)
        + abs(point[1] - center_y) / (half_height - tol)
    ) < 1.0


def segment_crosses_diamond_interior(
    start: tuple[float, float], end: tuple[float, float], bounds: Rect
) -> bool:
    # A connector segment is linear between validator samples. Sampling that segment
    # densely is deterministic and avoids treating the diamond's empty bounding-box
    # corners as node interior.
    length = point_distance(start, end)
    samples = max(2, int(length / 2) + 1)
    return any(
        point_inside_diamond((
            start[0] + (end[0] - start[0]) * step / samples,
            start[1] + (end[1] - start[1]) * step / samples,
        ), bounds)
        for step in range(samples + 1)
    )


def segment_crosses_node_interior(
    start: tuple[float, float], end: tuple[float, float], bounds: Rect, shape: str
) -> bool:
    if shape == "decision":
        return segment_crosses_diamond_interior(start, end, bounds)
    return segment_crosses_interior(start, end, bounds)


def boundary_crosses_node(boundary: Rect, node: Rect) -> bool:
    sides = [
        ((boundary.x, boundary.y), (boundary.right, boundary.y)),
        ((boundary.right, boundary.y), (boundary.right, boundary.bottom)),
        ((boundary.right, boundary.bottom), (boundary.x, boundary.bottom)),
        ((boundary.x, boundary.bottom), (boundary.x, boundary.y)),
    ]
    return any(segment_crosses_interior(a, b, node, 0.0) for a, b in sides)


def point_distance(first: tuple[float, float], second: tuple[float, float]) -> float:
    return ((first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2) ** 0.5


def path_length(points: list[tuple[float, float]]) -> float:
    return sum(point_distance(start, end) for start, end in zip(points, points[1:]))


def normalized_direction(start: tuple[float, float], end: tuple[float, float]) -> tuple[int, int]:
    dx, dy = movement(start, end)
    return (0 if abs(dx) <= 1e-6 else (1 if dx > 0 else -1),
            0 if abs(dy) <= 1e-6 else (1 if dy > 0 else -1))


def first_turn_point(geometry: PathGeometry) -> tuple[float, float] | None:
    if geometry.curved or len(geometry.points) < 3:
        return None
    previous = normalized_direction(geometry.points[0], geometry.points[1])
    for index in range(1, len(geometry.points) - 1):
        following = normalized_direction(geometry.points[index], geometry.points[index + 1])
        if following != previous:
            return geometry.points[index]
        previous = following
    return None


def rectangles_overlap(first: Rect, second: Rect) -> bool:
    return (
        max(first.x, second.x) < min(first.right, second.right)
        and max(first.y, second.y) < min(first.bottom, second.bottom)
    )


def axis_overlap_length(
    first_start: tuple[float, float], first_end: tuple[float, float],
    second_start: tuple[float, float], second_end: tuple[float, float]
) -> float:
    if abs(first_start[1] - first_end[1]) <= 1e-6 and abs(second_start[1] - second_end[1]) <= 1e-6:
        if abs(first_start[1] - second_start[1]) > TOLERANCE:
            return 0.0
        return max(0.0, min(max(first_start[0], first_end[0]), max(second_start[0], second_end[0]))
                   - max(min(first_start[0], first_end[0]), min(second_start[0], second_end[0])))
    if abs(first_start[0] - first_end[0]) <= 1e-6 and abs(second_start[0] - second_end[0]) <= 1e-6:
        if abs(first_start[0] - second_start[0]) > TOLERANCE:
            return 0.0
        return max(0.0, min(max(first_start[1], first_end[1]), max(second_start[1], second_end[1]))
                   - max(min(first_start[1], first_end[1]), min(second_start[1], second_end[1])))
    return 0.0


def shared_segment_length(first: PathGeometry, second: PathGeometry) -> float:
    axis_total = sum(
        axis_overlap_length(a1, a2, b1, b2)
        for a1, a2 in zip(first.points, first.points[1:])
        for b1, b2 in zip(second.points, second.points[1:])
    )
    suffix_total = 0.0
    first_index = len(first.points) - 1
    second_index = len(second.points) - 1
    while first_index > 0 and second_index > 0:
        if point_distance(first.points[first_index], second.points[second_index]) > TOLERANCE:
            break
        previous_first = first.points[first_index - 1]
        previous_second = second.points[second_index - 1]
        if point_distance(previous_first, previous_second) > TOLERANCE:
            break
        suffix_total += min(
            point_distance(previous_first, first.points[first_index]),
            point_distance(previous_second, second.points[second_index]),
        )
        first_index -= 1
        second_index -= 1
    return max(axis_total, suffix_total)


def is_arrowed_path(path: ET.Element) -> bool:
    classes = set((path.get("class") or "").split())
    return bool(path.get("marker-end") or classes.intersection({"connector", "conditional"}))


def connector_records(root: ET.Element, nodes: dict[str, Rect]) -> list[ConnectorRecord]:
    records: list[ConnectorRecord] = []
    for index, path in enumerate(root.iter(f"{SVG_NS}path"), start=1):
        source_id = path.get("data-from")
        target_id = path.get("data-to")
        source_side = path.get("data-from-side")
        target_side = path.get("data-to-side")
        if not source_id or not target_id or source_id not in nodes or target_id not in nodes:
            continue
        if source_side not in SIDE_NAMES or target_side not in SIDE_NAMES:
            continue
        try:
            geometry = parse_connector_path(path.get("d") or "")
        except ValueError:
            continue
        records.append(ConnectorRecord(
            path.get("id") or f"path#{index}", source_id, target_id,
            source_side, target_side, is_arrowed_path(path),
            frozenset((path.get("class") or "").split()), geometry,
        ))
    return records


def inside_canvas(point: tuple[float, float], canvas: Rect, tol: float = TOLERANCE) -> bool:
    return (
        canvas.x - tol <= point[0] <= canvas.right + tol
        and canvas.y - tol <= point[1] <= canvas.bottom + tol
    )


def validate_connectors(
    root: ET.Element, nodes: dict[str, Rect], node_shapes: dict[str, str], canvas: Rect | None
) -> list[str]:
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
            errors.append(f"{edge_id}: source node {source_id!r} has no supported geometry")
            continue
        if target_id not in nodes:
            errors.append(f"{edge_id}: target node {target_id!r} has no supported geometry")
            continue

        try:
            geometry = parse_connector_path(path.get("d") or "")
        except ValueError as exc:
            errors.append(f"{edge_id}: {exc}")
            continue

        points = geometry.points
        source_rect = nodes[source_id]
        target_rect = nodes[target_id]
        if not on_side(points[0], source_rect, source_side, node_shapes[source_id]):
            errors.append(f"{edge_id}: start point is detached from {source_id}.{source_side}")
        if not on_side(points[-1], target_rect, target_side, node_shapes[target_id]):
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
            if any(
                segment_crosses_node_interior(a, b, rect, node_shapes[node_id])
                for a, b in zip(points, points[1:])
            ):
                errors.append(f"{edge_id}: connector crosses unrelated node {node_id}")
    return errors


def validate_decisions(root: ET.Element, nodes: dict[str, Rect]) -> list[str]:
    errors: list[str] = []
    decision_ids = {
        group.get("id")
        for group in root.iter(f"{SVG_NS}g")
        if group.get("id") and group.get("data-node-shape") == "decision"
    }
    for decision_id in sorted(decision_ids):
        if decision_id not in nodes:
            errors.append(f"{decision_id}: decision geometry is unsupported or malformed")
            continue
        outgoing = [
            path for path in root.iter(f"{SVG_NS}path")
            if path.get("data-from") == decision_id and is_arrowed_path(path)
        ]
        if len(outgoing) < 2:
            errors.append(f"{decision_id}: decision gateway requires at least two arrowed outcomes")
        targets = {path.get("data-to") for path in outgoing if path.get("data-to")}
        if len(outgoing) >= 2 and len(targets) < 2:
            errors.append(f"{decision_id}: decision outcomes must lead to distinct target nodes")
        for path in outgoing:
            if not (path.get("data-label") or "").strip():
                edge_id = path.get("id") or "unnamed decision edge"
                errors.append(f"{edge_id}: decision outcome requires non-empty data-label")
    return errors


def validate_convergence(
    root: ET.Element, nodes: dict[str, Rect]
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    records = connector_records(root, nodes)
    hub_ids = {
        group.get("id")
        for group in root.iter(f"{SVG_NS}g")
        if group.get("id") and "routing-hub" in set((group.get("class") or "").split())
    }

    for record in records:
        if not record.arrowed and not record.classes.intersection({"converging", "leader"}):
            errors.append(
                f"{record.edge_id}: arrowless contracted route must be a converging input or explanatory leader"
            )
        if "converging" not in record.classes:
            continue
        if record.arrowed:
            errors.append(f"{record.edge_id}: converging inbound route must not carry an arrowhead")
        if record.target_id not in hub_ids:
            errors.append(f"{record.edge_id}: converging inbound route must terminate at a routing-hub")

    for hub_id in sorted(hub_ids):
        incoming = [record for record in records
                    if record.target_id == hub_id and "converging" in record.classes]
        outgoing = [record for record in records
                    if record.source_id == hub_id and record.arrowed]
        other_arrowed_incoming = [record for record in records
                                  if record.target_id == hub_id and record.arrowed]
        if len(incoming) < 2:
            errors.append(f"{hub_id}: routing hub requires at least two arrowless converging inputs")
        if len(outgoing) != 1:
            errors.append(f"{hub_id}: routing hub requires exactly one arrowed outbound connector")
        if other_arrowed_incoming:
            errors.append(
                f"{hub_id}: inbound routes must be arrowless; found "
                + ", ".join(record.edge_id for record in other_arrowed_incoming)
            )

    direct = [record for record in records if record.arrowed and record.source_id not in hub_ids]
    for index, first in enumerate(direct):
        for second in direct[index + 1:]:
            targets_overlap = (
                first.target_id == second.target_id
                or rectangles_overlap(nodes[first.target_id], nodes[second.target_id])
            )
            if not targets_overlap:
                continue

            pair_name = f"{first.edge_id} + {second.edge_id}"
            if first.source_side == second.source_side:
                warnings.append(
                    f"{pair_name}: same source side and same/overlapping target region; "
                    f"inspect shared-segment risk or use single-arrow convergence"
                )

            first_turn = first_turn_point(first.geometry)
            second_turn = first_turn_point(second.geometry)
            if first_turn is not None and second_turn is not None:
                turn_gap = point_distance(first_turn, second_turn)
                if turn_gap < VISUAL_SEPARATION:
                    warnings.append(
                        f"{pair_name}: first turn points are only {turn_gap:.1f}px apart "
                        f"(< {VISUAL_SEPARATION:.0f}px)"
                    )

            shared = shared_segment_length(first.geometry, second.geometry)
            shorter = min(path_length(first.geometry.points), path_length(second.geometry.points))
            shared_ratio = shared / shorter if shorter > 0 else 0.0
            if shared >= MIN_SHARED_LENGTH and shared_ratio > MAX_SHARED_RATIO:
                errors.append(
                    f"{pair_name}: arrowed connectors share {shared:.1f}px "
                    f"({shared_ratio:.0%} of the shorter route); use separate routes or "
                    f"single-arrow convergence"
                )

    return errors, warnings


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

    nodes, node_shapes, node_warnings = node_geometries(root)
    warnings.extend(node_warnings)
    errors.extend(validate_connectors(root, nodes, node_shapes, canvas))
    errors.extend(validate_decisions(root, nodes))
    convergence_errors, convergence_warnings = validate_convergence(root, nodes)
    errors.extend(convergence_errors)
    warnings.extend(convergence_warnings)
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
