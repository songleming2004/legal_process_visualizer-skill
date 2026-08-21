# Editable SVG standard for legal diagrams

Read this reference whenever creating or materially revising an SVG deliverable.

## Document structure

Use this order:

1. root `<svg>` with `xmlns`, physical dimensions, `viewBox`, and accessibility attributes;
2. `<title>` and `<desc>`;
3. `<defs>` containing arrow markers, optional filters, and shared styles;
4. neutral background if the user wants a document-like page;
5. title and subtitle;
6. connectors;
7. lanes and nodes grouped by descriptive IDs;
8. legend, assumptions, source version, and effective date.

Keep the source readable. One legal step should normally be one `<g id="...">` containing its rectangle or decision shape and all related text.

## Text

- Use `<text>` and `<tspan>` so labels remain editable.
- Prefer fonts commonly available in the target environment, with fallbacks such as `Noto Sans SC`, `PingFang SC`, `Microsoft YaHei`, and `sans-serif`.
- Use no more than three text levels: title, node heading, and body/source.
- Keep authority on its own final line and wrap it in parentheses.
- Do not shrink citations until they become unreadable; enlarge the node or canvas instead.
- Avoid `foreignObject` unless rich wrapping is indispensable and the target editor supports it.

## Geometry

- Use consistent node widths within a lane.
- Keep vertical gaps sufficient for arrowheads and labels.
- Attach arrows to node boundaries, not through node centers.
- Give every arrowed connector a stable ID and declare `data-from`, `data-to`, `data-from-side`, and `data-to-side`. The declared node IDs must exist.
- Calculate connector endpoints from node geometry. Do not type a coordinate merely because it looks close to a node.
- Route the final segment from outside the target toward the declared side. A path that lands on the right boundary while still pointing right is invalid even though its endpoint touches the rectangle.
- Put conditional labels near the first segment leaving a decision diamond.
- Apply the line-semantics rules below; do not dash a connector merely because it is outside the main path.
- Avoid connector crossings. If unavoidable, use lanes, bridge spacing, or split the diagram.

Read [connector-integrity.md](connector-integrity.md) for the connector data contract, pre-render checks, collision rules, and enlarged-crop triggers.

## Line semantics

Use line style to encode the nature of a relationship and color to encode the procedure category. Do not use either as decoration or overload one style with several meanings.

- **Solid arrow:** ordinary procedural progression or any transition that changes the legal or procedural state.
- **Dashed arrow:** conditional, exceptional, discretionary, optional, or procedure-conversion route. Label every non-obvious dashed arrow with the condition or route type.
- **Dashed leader without an arrowhead:** association with an explanatory note, source note, citation, or `易错提示`. It does not indicate procedural direction.
- **Dashed border:** scope, group, or module boundary. It does not indicate a legal relationship between enclosed nodes.
- Return, remand, reconsideration, review, appeal, referral, and similar routes must use directional arrows whenever they change state, even when they are outside the main path.
- Color encodes procedure category; line style encodes relationship nature. Do not swap, combine, or duplicate these meanings.
- Include a line-style legend whenever more than one line style appears.

## Color

Use color to encode procedure category, not individual decoration. A reusable light palette is:

```text
page:        #F7F6F2
text:        #1F2933
structure:   #55606D
first-stage: #E7EEF6 / border #6783A2
review:      #EEE9F5 / border #86729F
accelerated: #E5F0EA / border #668B78
publication: #F4ECDC / border #A48755
risk:        #F3E5E2 / border #A66F67
neutral:     #ECEFF1 / border #84909A
```

Use different lane headings or text labels in addition to color. Maintain sufficient text contrast.

## Editability and portability

- Do not convert text to outlines.
- Do not flatten the diagram into one path.
- Avoid editor-specific namespaces unless the user requests them.
- Do not embed remote fonts or external images in a self-contained legal file.
- Preserve semantic IDs and reusable classes.
- Include a source version line inside the canvas.

## Rendering checks

Run `scripts/validate_svg.py` before the first render and after every connector or geometry revision. Then inspect a rendered preview at full-page scale, at a readable zoom, and in enlarged connector crops. Check:

- text overflow or clipping;
- missing glyphs, especially `§`, Chinese punctuation, and en dashes;
- arrows hidden behind nodes;
- branches that appear to lead to the wrong outcome;
- inconsistent margins or node heights;
- citations that are too small to read;
- content below the viewBox;
- accidental rasterization or text converted to paths.

Do not treat a clean full-page thumbnail as proof that connectors are correct. At full-page scale, a small detached endpoint or wrong approach direction can be visually subtle.
