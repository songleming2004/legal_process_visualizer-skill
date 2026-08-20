# Detail, coverage, and reference benchmarking

Read this reference for a complete-process visual, a dense visual, a visual intended to match a supplied reference, or any project where omission risk is material.

## Choose a detail profile

Use the least compressed profile that matches the user's purpose.

### Overview

- Show the main procedural posture and major exits.
- One node may summarize a stage or a short group of provisions.
- Use only when the user wants orientation rather than provision-level coverage.

### Provision-level

- Represent each operative rule that changes an actor, trigger, required or permitted act, deadline, consequence, branch, exception, prohibition, or remedy.
- Do not use a broad citation range as a substitute for materially different rules.
- Prefer separate child nodes over dense prose inside one card.

### Practice-oriented

- Start with the provision-level model.
- If the user approves the expanded source scope, add relevant judicial interpretations and departmental case-handling rules.
- Show responsible bodies, approvals, forms, service, records, operational exceptions, and review mechanisms when supported by the approved sources.

### Dense study-scroll

- Start with the provision-level or practice-oriented model selected by the user.
- Combine the main flow with comparison matrices, procedure-conversion diagrams, exception lists, authority hierarchies, deadline summaries, and error-prone-point callouts.
- Preserve source distinctions. High density does not justify presenting a teaching simplification as a legal rule.

If a user asks for a complete process, permits an unlimited canvas, and does not otherwise choose a profile, recommend provision-level. Ask before using practice-oriented sources or dense study-scroll treatment.

## Confirm supplemental source scope

Before researching or modeling sources beyond the governing instrument named by the user:

1. identify the supplemental source categories likely to change the requested visual;
2. ask whether the user wants them included;
3. explain briefly that including them increases operational detail and may add exceptions or different deadlines;
4. record the user's choice in the coverage manifest.

Do not ask about unrelated source categories. Do not silently treat a judicial interpretation or departmental rule as part of the statute.

## Build a coverage manifest before drawing

For every in-scope unit, retain:

- stable coverage ID;
- instrument and exact provision, paragraph, and subparagraph;
- short legal subject;
- planned treatment: `独立节点`, `子节点`, `总览节点`, or `省略`;
- planned node ID or diagram name;
- source/content label;
- omission reason when omitted;
- notes on overlap, conflict, supersession, or uncertainty.

The manifest may be Markdown, CSV, JSON, or a spreadsheet, but it must be reviewable. A chapter title alone is not a coverage unit when its provisions contain materially different operative rules.

Before delivery, reconcile the manifest in both directions:

- every in-scope unit has a treatment;
- every substantive visual node maps to at least one authority or a clearly identified `易错提示`;
- every omitted unit has a reason;
- no source outside the user-approved scope appears without explanation.

## Apply granularity rules

Except in overview mode:

- do not cite more than three consecutive provisions in one node when those provisions contain different actors, conditions, deadlines, acts, consequences, exceptions, prohibitions, or remedies;
- split a rule when a reader must answer different legal questions to traverse it;
- separate an entry condition from the act it authorizes when either has exceptions;
- separate the decision-maker from the executor when they differ;
- separate a deadline from an extension, exclusion, tolling rule, or recalculation event;
- separate an ordinary route from an exceptional or accelerated route;
- give every remedy, review, appeal, remand, return, dismissal, release, and enforcement outcome a visible destination;
- keep prohibitions and adverse consequences visually distinct from ordinary steps.

The preferred legal unit is not “one article per card.” It is one coherent rule or decision per node, with child nodes for conditions and exceptions where that improves traversal.

## Use mixed legal information architecture

Choose the form that matches the relationship:

- directed flow for sequence and state change;
- decision tree for mutually exclusive legal conditions;
- swimlanes for actor responsibility;
- timeline for triggering events, periods, extensions, and tolling;
- matrix for repeated comparisons such as ordinary, simplified, and accelerated tracks;
- authority tree for institutional hierarchy or review routes;
- exception list for rules that interrupt a common path;
- procedure-conversion diagram when cases can move between tracks;
- callout for a genuinely error-prone point that should not interrupt the main path.

Do not force all content into equal-height cards. Keep ordinary SVG text editable and keep the main procedural direction unambiguous.

## Use the label system

Use only these visible labels for source type or explanatory emphasis:

- `法条明文`: a statute or other enacted legal provision stated directly;
- `司法解释`: an operative judicial interpretation;
- `部门办案规则`: a departmental or institutional case-handling rule;
- `易错提示`: a concise caution about a likely misunderstanding.

The label supplements, but never replaces, an exact citation. An `易错提示` must not be drawn as though it independently creates authority.

## Benchmark a supplied reference

Before matching a supplied visual, record:

- physical and viewBox dimensions;
- number of diagrams, sections, lanes, and visible information units;
- approximate branch depth and number of terminal outcomes;
- source categories used;
- proportion of sequence nodes, condition lists, comparison matrices, deadline summaries, exception notes, and callouts;
- typography range and the smallest readable text at the intended use size;
- how the reference handles cross-links, repeated rules, legends, and source attribution;
- which reference features are content choices and which are merely aesthetic.

Use the benchmark to set density and architecture. Do not copy a reference's omissions, ambiguous arrows, unsupported summaries, or unreadable typography merely to imitate it.

## Run a pilot-stage checkpoint

For a large complete-process project:

1. build the coverage manifest for the whole approved scope;
2. select a representative stage with deadlines, branches, exceptions, and at least two actors;
3. produce that stage at the chosen detail profile;
4. ask the user to confirm granularity, source labels, citation density, and layout before batch drawing.

Skip the checkpoint only when the user explicitly waives it. A supplied reference controls the benchmark but does not by itself waive confirmation.

## Audit legal completeness before delivery

Perform and record these audits in addition to SVG structural validation:

### Coverage audit

- all in-scope units are mapped or intentionally omitted;
- all visual nodes map back to approved sources or an `易错提示`;
- overview nodes are identified as summaries rather than exhaustive treatment.

### Deadline audit

- every deadline includes its actor, duration, unit, triggering event, and consequence when stated;
- extensions, exclusions, tolling, and recalculation events are separate and correctly linked;
- arithmetic totals are not presented as legal deadlines.

### Branch audit

- every condition has all material outcomes;
- exceptions rejoin the correct route or terminate visibly;
- dismissal, release, return, remand, appeal, review, enforcement, and settlement paths do not disappear.

### Source audit

- every source is within the user-approved scope;
- source labels match the instrument type;
- conflicts, superseded versions, and uncertainty are disclosed;
- an `易错提示` does not masquerade as authority.

Do not claim completeness merely because an SVG validator passes. Structural validity and legal completeness are different checks.
