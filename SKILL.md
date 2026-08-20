---
name: legal-process-visualizer
description: Research, structure, and create or revise editable legal-process visualizations—including litigation, arbitration, administrative, regulatory, self-regulatory, appellate, enforcement, evidence, and deadline flows—when the user asks for a procedural flowchart, litigation timeline, decision tree, source-cited diagram, or editable SVG. Do not use for ordinary legal prose without a visual deliverable.
---

# Legal Process Visualizer

Create legally accurate visuals that let a reader see actors, procedural posture, triggers, deadlines, branches, authority, publication, appeal, enforcement, and uncertainty without confusing a private process with state power or an inference with a rule.

## Align on the requested effect

Before drawing a new visual, resolve only the choices that materially affect the result. If the user has not already supplied them, ask concisely about:

- scope and jurisdiction;
- one complete diagram or several coordinated diagrams;
- output format and editability;
- visual tone and color treatment;
- detail profile, especially whether the visual is an overview, provision-level map, practice map, or dense study scroll;
- whether to rely only on the named governing instrument or also include potentially relevant judicial interpretations, departmental case-handling rules, and other supplemental sources;
- level of detail for deadlines and authorities.

Do not generate a mind map merely because the user asks for “mind-map-like colors.” Treat color language and layout language separately. Default to a directed flowchart, swimlane, timeline, or decision tree according to the legal relationship.

## Set detail, coverage, and source scope

Use one of four detail profiles: overview, provision-level, practice-oriented, or dense study-scroll. Do not default a request for a complete process to overview mode when the user allows a large canvas or asks for comprehensive detail.

Before expanding beyond the governing instrument named by the user, ask whether to include likely supplemental source categories. Name only the categories that are plausibly relevant to the proceeding, such as judicial interpretations or departmental case-handling rules. Do not silently enlarge the source scope.

For a complete-process or reference-matching project, read [references/detail-coverage-and-benchmarking.md](references/detail-coverage-and-benchmarking.md) before modeling. It defines the detail profiles, coverage manifest, granularity rules, source labels, reference benchmark, mixed information architecture, pilot-stage checkpoint, and completeness audit.

## Establish the legal model before drawing

1. Identify the jurisdiction, forum, governing instrument, version or effective date, procedural track, and requested start/end points.
2. Prefer current primary sources. Verify unstable rules, fees, deadlines, agency guidance, and procedural versions before using them.
3. For a complete-process visual, create a coverage manifest before drawing. Map every in-scope chapter, section, provision, paragraph, or other operative unit to a planned node, an overview-only treatment, or an explained omission.
4. Extract each legally meaningful item into this schema:
   - **actor**;
   - **trigger or entry condition**;
   - **required or permitted act**;
   - **deadline and start event**;
   - **authority**;
   - **output or state change**;
   - **next branch**;
   - **exception, tolling rule, or uncertainty**.
5. Distinguish:
   - mandatory (`shall`, `must`) from discretionary (`may`);
   - calendar days from business or court days;
   - a period from its triggering event;
   - a legal deadline from a calculated total duration;
   - a formal rule from common practice, inference, or an observed publication pattern;
   - adjudication from appeal, compliance, enforcement, referral, and publication;
   - governmental authority from contractual, arbitral, professional, or industry self-regulation.
6. Never invent a missing deadline. Label it “规则未规定／未设固定期限” and cite the provision that creates the step when possible.

For detailed source and deadline handling, read [references/legal-source-and-time.md](references/legal-source-and-time.md).

## Choose the smallest useful diagram set

Use one diagram when the main sequence remains readable. Split it when appeal, publication, enforcement, evidence, or multiple tracks would otherwise make the central path difficult to follow.

When the user does not limit size, do not compress substantive rules to fit a preset canvas. Expand the canvas, add coordinated diagrams, or use nested regions. Never remove a condition, exception, remedy, or authority merely to preserve a preferred page size.

Useful coordinated sets include:

- main proceeding;
- notice, service, publication, or disclosure;
- appeal and review;
- compliance, enforcement, execution, or referral;
- evidence and burden of proof;
- limitations and deadline timeline.

Use stable lanes for actors or procedural tracks. Use branches for legal choices or factual conditions, not merely to decorate the diagram. Label every non-obvious edge (`是／否`, `可选`, `转介`, `上诉`, `发回`, `中止`).

Uniform flowchart cards are not mandatory. When density or comparison requires it, combine a main flow with condition matrices, deadline timelines, authority tables, exception lists, procedure-conversion diagrams, and clearly separated error-prone-point callouts. Keep the legal relationship, not visual uniformity, as the organizing principle.

For litigation and other recurring legal patterns, read only the relevant parts of [references/legal-diagram-models.md](references/legal-diagram-models.md).

## Put authority inside the visual

Each substantive node should contain, in this order when space permits:

1. step name;
2. actor and act;
3. deadline and triggering event;
4. consequence or next state;
5. parenthetical authority.

Format authority as a separate final line using parentheses, for example:

`（依据：《Rules of Civil Procedure》Rule 12(a)(1)(A)）`

or, in a compact diagram:

`（Rule 12(a)(1)(A)）`

Do not introduce the authority with a colon. Preserve exact section, rule, article, paragraph, and subparagraph structure. When one visual mixes source types, visibly mark non-rule content:

- `（时间推算；依据：Rules 6、12）`
- `（公开实践；非规则明文）`
- `（规则未规定固定期限）`

If the user needs auditability, accompany the visual with a Markdown source table mapping node IDs to exact provisions, source links, effective dates, and any interpretive notes.

For a complete-process visual, this node-to-source index and the coverage manifest are mandatory rather than optional.

When multiple source types or explanatory callouts appear, use only these visible source/content labels:

- `法条明文`;
- `司法解释`;
- `部门办案规则`;
- `易错提示`.

Do not present an `易错提示` as binding authority. Connect it to the supporting rule when one exists, and keep the exact authority in the node or source index.

## Produce editable legal SVGs

When editable SVG is requested:

- keep labels as `<text>` and `<tspan>`, never convert them to paths;
- group every node and lane with descriptive IDs;
- use a `viewBox`, reusable CSS classes, `<defs>`, and marker-based arrows;
- include `<title>` and `<desc>` for accessibility;
- avoid embedded raster images unless the user specifically needs them;
- avoid `foreignObject` when ordinary SVG text can preserve editor compatibility;
- keep connectors behind nodes and attach arrows cleanly to node boundaries;
- avoid crossed connectors, clipped labels, and ambiguous arrow direction;
- use line style only for relationship nature: solid arrows for ordinary or other state-changing transitions, dashed arrows for conditional, exceptional, optional, or procedure-conversion routes, arrowless dashed leaders for explanatory associations, and dashed borders for module or scope boundaries;
- use low-saturation category colors with neutral structural lines;
- pair color with headings or lane labels so color is not the only encoding;
- preserve a formal legal-document tone even when using several category colors.

Recommended category mapping:

- ordinary first-instance steps: muted blue;
- complex, appellate, or review steps: muted violet;
- accelerated or compliance steps: muted green;
- publication or terminal outcomes: muted sand;
- default, refusal, sanction, or referral risk: muted red;
- common intake and neutral notes: gray.

Start from [assets/editable-legal-flow-template.svg](assets/editable-legal-flow-template.svg) when it materially saves work. Read [references/editable-svg-standard.md](references/editable-svg-standard.md) before creating or substantially revising an SVG.

## Verify before delivery

1. Reconcile every node against the governing source.
2. Reconcile the final node set against the coverage manifest. Every omission must be intentional and explained.
3. Check that every deadline shows its triggering event and unit.
4. Check every condition, exception, prohibition, consequence, remedy, and procedure-conversion path for a visible destination.
5. Check branches for missing outcomes, especially dismissal, default, tolling, appeal, remand, settlement, referral, and enforcement.
6. For a large complete-process project, first produce one representative stage at the chosen detail profile and obtain the user's confirmation before batch drawing, unless the user explicitly waives the checkpoint.
7. Validate SVG structure with:

   `python3 scripts/validate_svg.py <file-or-directory>`

8. Render each SVG to a raster preview and inspect the full image for clipping, overflow, connector collisions, unreadable citations, and inconsistent spacing.
9. Keep the SVG as the editable source. A PNG is only a preview.
10. Deliver each file with a descriptive name and state the governing source version or effective date.

Do not claim completeness if a source was unavailable, a deadline remains disputed, or the visual intentionally omits a track. State the limitation in the diagram or handoff.
