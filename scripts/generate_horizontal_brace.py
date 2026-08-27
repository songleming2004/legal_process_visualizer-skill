#!/usr/bin/env python3
"""Generate a font-like horizontal SVG brace without distorting its anatomy.

The normalized silhouette is derived from the `llv` curly-brace path in
assets/typographic-brace-reference.svg. Lengthening is applied only to the two
straight arm regions; terminal heads, shoulders, and the central waist retain
their proportions.
"""

from __future__ import annotations

import argparse


BASE_WIDTH = 188.0
BASE_DEPTH = 56.0

# Commands after rotating the reference's vertical right brace 90 degrees
# counterclockwise and translating it to a local 0,0 origin.
COMMANDS = [
    ("M", ((0, 0),)),
    ("L", ((0, 5),)),
    ("C", ((0, 11), (0, 15), (1, 19))),
    ("C", ((2, 23), (5, 27), (9, 30))),
    ("C", ((13, 33), (17, 34), (22, 35))),
    ("C", ((27, 36), (36, 36), (48, 36))),
    ("C", ((57, 36), (63, 36), (68, 37))),
    ("C", ((73, 38), (78, 40), (81, 43))),
    ("C", ((84, 46), (86, 50), (86, 56))),
    ("L", ((102, 56),)),
    ("C", ((102, 50), (104, 46), (107, 43))),
    ("C", ((110, 40), (115, 38), (120, 37))),
    ("C", ((125, 36), (131, 36), (140, 36))),
    ("C", ((152, 36), (161, 36), (166, 35))),
    ("C", ((171, 34), (175, 33), (179, 30))),
    ("C", ((183, 27), (186, 23), (187, 19))),
    ("C", ((188, 15), (188, 11), (188, 5))),
    ("L", ((188, 0),)),
    ("L", ((173, 0),)),
    ("L", ((173, 3),)),
    ("C", ((173, 10), (172, 14), (170, 16))),
    ("C", ((167, 19), (166, 20), (163, 20))),
    ("L", ((138, 20),)),
    ("C", ((123, 20), (113, 22), (107, 25))),
    ("C", ((101, 28), (97, 34), (94, 40))),
    ("C", ((91, 34), (87, 28), (81, 25))),
    ("C", ((75, 22), (65, 20), (50, 20))),
    ("L", ((25, 20),)),
    ("C", ((22, 20), (21, 19), (18, 16))),
    ("C", ((16, 14), (15, 10), (15, 3))),
    ("L", ((15, 0),)),
    ("Z", ()),
]


def number(value: float, decimals: int) -> str:
    rounded = round(value, decimals)
    if abs(rounded) < 10 ** (-decimals):
        rounded = 0.0
    return f"{rounded:.{decimals}f}".rstrip("0").rstrip(".")


def stretched_x(x: float, length: float, scale: float) -> float:
    """Preserve fixed anatomy and distribute extra length across both arms."""
    scaled = x * scale
    base_width = BASE_WIDTH * scale
    extra = length - base_width
    if x <= 50:
        return scaled
    if x < 81:
        source_start = 50 * scale
        source_width = 31 * scale
        target_width = source_width + extra / 2
        return source_start + (scaled - source_start) * target_width / source_width
    if x <= 107:
        return scaled + extra / 2
    if x < 138:
        source_start = 107 * scale
        source_width = 31 * scale
        target_start = source_start + extra / 2
        target_width = source_width + extra / 2
        return target_start + (scaled - source_start) * target_width / source_width
    return scaled + extra


def weighted_inner_point(x: float, y: float, weight: float) -> tuple[float, float]:
    """Thin the inner contour while preserving the outer depth and endpoints."""
    if weight == 1:
        return x, y

    # The reference silhouette has an approximately 16-unit gap between its
    # outer and inner contours. Move only the inner contour toward the outer
    # contour; taper the correction near the terminal baseline so the flat
    # heads remain recognizable.
    if y > 0:
        y += 16 * (1 - weight) * min(y / 20, 1)

    terminal_shift = 15 * (1 - weight)
    if x <= 25:
        strength = max(0.0, min(1.0, (25 - x) / 10))
        x -= terminal_shift * strength
    elif x >= 163:
        strength = max(0.0, min(1.0, (x - 163) / 10))
        x += terminal_shift * strength
    return x, y


def make_path(
    x1: float,
    x2: float,
    y: float,
    depth: float,
    orientation: str,
    decimals: int,
    weight: float = 1.0,
) -> str:
    length = x2 - x1
    if length <= 0:
        raise ValueError("x2 must be greater than x1")
    if depth <= 0:
        raise ValueError("depth must be positive")
    if not 0 < weight <= 1:
        raise ValueError("weight must be greater than 0 and at most 1")
    scale = depth / BASE_DEPTH
    minimum = BASE_WIDTH * scale
    if length < minimum:
        raise ValueError(
            f"span {length:g} is too short for depth {depth:g}; "
            f"minimum without anatomical compression is {minimum:.2f}"
        )
    direction = 1 if orientation == "under" else -1

    parts: list[str] = []
    for index, (command, points) in enumerate(COMMANDS):
        parts.append(command)
        for px, py in points:
            # Command 18 starts the returning inner contour. The outer contour
            # stays fixed so reducing weight changes visible body thickness,
            # not the brace's overall depth.
            if index >= 18:
                px, py = weighted_inner_point(px, py, weight)
            tx = x1 + stretched_x(px, length, scale)
            ty = y + direction * py * scale
            parts.append(f"{number(tx, decimals)} {number(ty, decimals)}")
    return " ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--x1", type=float, required=True)
    parser.add_argument("--x2", type=float, required=True)
    parser.add_argument("--y", type=float, required=True, help="terminal-head baseline")
    parser.add_argument("--depth", type=float, default=56.0)
    parser.add_argument(
        "--weight",
        type=float,
        default=1.0,
        help="inner-contour weight from 0 to 1; 0.55 is visibly lighter",
    )
    parser.add_argument("--orientation", choices=("under", "over"), default="under")
    parser.add_argument("--decimals", type=int, default=2)
    args = parser.parse_args()
    print(
        make_path(
            args.x1,
            args.x2,
            args.y,
            args.depth,
            args.orientation,
            args.decimals,
            args.weight,
        )
    )


if __name__ == "__main__":
    main()
