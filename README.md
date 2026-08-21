# Legal Process Visualizer

[English](README.md) | [简体中文](README.zh-CN.md)

An editable, source-aware legal-process visualization skill for Codex. It helps research, model, create, revise, and verify litigation, arbitration, administrative, regulatory, appellate, enforcement, evidence, deadline, and legal-relationship diagrams.

## What it does

- Models actors, triggers, acts, deadlines, authority, outputs, branches, exceptions, and uncertainty before drawing.
- Creates editable SVGs with live text, descriptive IDs, reusable styles, and marker-based arrows.
- Keeps governing authority visible in the diagram and supports node-to-source indexes for auditable work.
- Distinguishes procedural transitions, conditional routes, explanatory associations, and module boundaries by line semantics.
- Validates connector identity, boundary attachment, direction, unrelated-node crossings, and module-boundary collisions before rendering.
- Supports overview, provision-level, practice-oriented, and dense study-scroll detail profiles.

## Install

Clone the repository:

```bash
git clone https://github.com/songleming2004/legal_process_visualizer-skill.git
```

Copy the skill contents into your Codex skills directory. Keep the installed skill folder name as `legal-process-visualizer`:

```bash
mkdir -p ~/.codex/skills/legal-process-visualizer
rsync -a --exclude .git --exclude 'README*' legal_process_visualizer-skill/ ~/.codex/skills/legal-process-visualizer/
```

Restart or reload Codex if the skill is not detected immediately.

## Use

Invoke the skill explicitly:

```text
$legal-process-visualizer
Create three editable SVG diagrams from this judgment: a cross-jurisdiction timeline,
a procedural path, and a legal-relationship diagram. Use only the judgment as the source.
```

You can also ask for a procedural flowchart, litigation timeline, decision tree, source-cited diagram, or revision of an existing editable legal SVG.

## Connector contract

Every arrowed connector must identify its source node, target node, and attachment sides:

```svg
<path id="edge-application-order"
      class="connector"
      d="M320 300 V380"
      data-from="application"
      data-to="service-order"
      data-from-side="bottom"
      data-to-side="top"/>
```

Endpoints must lie on the declared node boundaries. The first segment must leave the source outward, and the final segment must approach the target inward. This prevents arrows that visually point into empty space or appear to belong to a nearby heading or node.

## Validate

Validate one SVG or a directory before rendering:

```bash
python3 scripts/validate_svg.py path/to/diagram.svg
python3 scripts/validate_svg.py path/to/svg-directory
```

The validator treats missing connector metadata, detached endpoints, incorrect approach direction, unrelated-node crossings, and module-boundary/node crossings as failures. Automated validation complements—rather than replaces—source reconciliation and enlarged visual inspection.

Validate the skill package itself with Codex's `skill-creator` validator:

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py .
```

## Repository structure

```text
SKILL.md                                  Core workflow and delivery requirements
assets/editable-legal-flow-template.svg   Editable starter SVG
references/connector-integrity.md         Connector contract and inspection rules
references/editable-svg-standard.md       SVG construction and rendering standard
references/legal-*.md                     Legal modeling and source guidance
scripts/validate_svg.py                   Structural and connector validator
```

## Scope note

This skill assists with legal research organization and visual communication. It does not replace jurisdiction-specific legal advice. State source limits, disputed deadlines, unavailable authorities, and intentionally omitted tracks in the diagram or delivery note.
