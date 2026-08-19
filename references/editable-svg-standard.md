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
- Put conditional labels near the first segment leaving a decision diamond.
- Route optional or exceptional paths with dashed lines, but do not dash every connector.
- Avoid connector crossings. If unavoidable, use lanes, bridge spacing, or split the diagram.

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

Inspect a rendered preview at full-page scale and at a readable zoom. Check:

- text overflow or clipping;
- missing glyphs, especially `§`, Chinese punctuation, and en dashes;
- arrows hidden behind nodes;
- branches that appear to lead to the wrong outcome;
- inconsistent margins or node heights;
- citations that are too small to read;
- content below the viewBox;
- accidental rasterization or text converted to paths.
