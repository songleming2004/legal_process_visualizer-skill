# Temporal spans and typographic-brace grammar

Read this reference when a legal visual contains a period, window, continuous factual state, interruption, suspension, tolling, legal-transition interval, nested interval, or requested long brace.

## Decide from the analytical task

Do not equate `legal period = brace` and `factual state = band`. First identify what the reader must see.

| Temporal object | Default expression | Use a brace instead when |
|---|---|---|
| accrual, filing, release, effective date, expiry | point or milestone | never; a point has no duration |
| statutory or court-recognized calculation interval | typographic brace | normally the default |
| continuous factual state, such as custody, incapacity, stay, possession, or authorization | state band | its start/end or overlap with another interval is the main question |
| legally relevant subset of a longer state | nested brace or coordinated shorter brace | both sets of endpoints must remain auditable |
| procedural phase grouping without elapsed-time meaning | module boundary or grouping brace | only when the label expressly says it is a phase rather than a duration |
| estimated or arithmetic total | brace with an explicit estimate label | assumptions and exclusions are shown visibly |

One diagram may combine these expressions. Shape identifies the reading task; color, labels, and authority identify legal nature.

## Brace semantic contract

Treat a temporal brace as an annotation, not a procedural connector or a legal actor. Give its group stable metadata such as:

```svg
<g id="custody-span"
   data-temporal-role="continuous-factual-obstacle"
   data-start="2016-08-15"
   data-end="2017-11-06"
   data-scale="month-level"
   data-authority="case-holding">
  ...
</g>
```

Every temporal brace must have:

- an identified start event and end event;
- dashed or otherwise unmistakable projections to the corresponding time-axis positions when the endpoints are not immediately adjacent to the axis;
- a label stating whether it is a legal period, court calculation, factual state, disputed span, phase grouping, or estimate;
- the exact authority or an explicit factual-source label in the brace card;
- an uncertainty or scale disclosure when dates are only month-level or the axis is approximate.

Do not place arrowheads on a brace. Do not let its curvature imply procedural direction.

## Geometry and orientation

Use a font-like filled silhouette when the requested reference resembles `{ }`. A valid typographic brace has:

- flat, short terminal heads;
- rounded shoulders after each terminal;
- a constant-looking filled body rather than a single stroked centerline;
- a pronounced central waist made from paired curves, not a pasted V notch;
- symmetrical geometry around the midpoint unless the source or user deliberately requests an asymmetric semantic anchor.

For an underbrace whose label is below the interval, both terminal heads turn upward toward the referenced timeline and the central waist points downward toward the label. Reverse both features for an overbrace.

Compute the central waist from the endpoint coordinates:

`midpoint = (start_x + end_x) / 2`

Do not place it by eye. If the waist intentionally identifies a different event, record that exception and do not describe the shape as a centered grouping brace.

Do not stretch a complete brace glyph uniformly to make it long. Uniform stretching deforms the heads, shoulders, and waist. Preserve those modules and extend only the straight arm regions. Use:

```bash
python3 scripts/generate_horizontal_brace.py \
  --x1 200 --x2 900 --y 500 --depth 54 --weight 0.55 --orientation under
```

The generator derives its silhouette from the curly-brace path in `assets/typographic-brace-reference.svg` and outputs an editable SVG path `d` value.

Treat depth and weight as separate controls. `--depth` sets the distance from the terminal baseline to the central waist. `--weight` thins only the returning inner contour while preserving the outer depth, endpoints, shoulders, and centered waist. Use `1` for the reference weight and approximately `0.5–0.65` for a visibly lighter brace. Do not claim that a small depth reduction has made the brace thinner when the difference is not perceptible at the delivery scale.

## Nested and overlapping intervals

When a factual span overlaps a legal window, choose the smallest structure that preserves both endpoint sets:

- one brace for the whole factual span plus a shorter coordinated brace for the legally relevant overlap;
- or a brace for the focal span plus a lightly filled band when continuous background state is also important.

Do not use one brace for two different endpoint pairs. Do not hide tolling, suspension, restart, or a legal-transition date inside a broad unlabeled span.

Use color-matched dashed projection guides selectively. Project every legally material start/end point, but avoid drawing guides for decorative or already-adjacent ticks. Shared endpoints should normally use one shared guide rather than coincident lines of different colors.

## Authority placement

Put the authority in the card associated with the span or transition. A footer source note does not replace node-level authority when the rule determines the interval.

For a legal-transition card, separate each operative proposition and its authority, for example:

```text
旧制期间未满 → 适用新期间规则
中止原因未消除 → 适用新中止规则
（完整司法解释名称及第 X、Y 条）
```

## Review checklist

1. Are both endpoints legally and geometrically correct?
2. Do projection guides meet the intended axis positions and brace heads?
3. Is the central waist exactly centered?
4. Are underbrace or overbrace heads oriented toward the referenced content?
5. Does the silhouette retain the reference head, shoulder, body, and waist proportions?
6. Are a whole span and any relevant subspan shown with separate endpoint pairs?
7. Does the label distinguish rule, court calculation, factual state, dispute, and estimate?
8. Is the governing authority inside the corresponding card?
9. After rendering, do filled brace heads remain recognizable at full-page scale and enlarged scale?
