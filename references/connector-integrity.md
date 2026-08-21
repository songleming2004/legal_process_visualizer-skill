# Connector integrity for editable legal SVGs

Read this reference whenever an SVG contains arrows, dashed conditional routes, relationship edges, cross-lane connectors, or module boundaries.

## Connector data contract

Each arrowed connector must have:

```svg
<path
  id="edge-application-hearing"
  data-from="application"
  data-to="hearing"
  data-from-side="bottom"
  data-to-side="top"
  class="connector"
  d="M320 320 V385"/>
```

- `data-from` and `data-to` refer to stable `<g id="…">` node IDs.
- `data-from-side` and `data-to-side` use only `top`, `right`, `bottom`, or `left`.
- The first path coordinate lies on the declared source boundary.
- The last path coordinate lies on the declared target boundary.
- Calculate both endpoints from node geometry. A small visual gap is still a failed connector.
- Arrowless explanatory leaders should declare `data-from` and `data-to` when both ends associate named nodes. They may omit side metadata only when they deliberately terminate at a label or non-node annotation.

## Approach direction

The final non-zero path segment must move from outside the target toward its declared side:

| Target side | Final movement |
|---|---|
| `left` | rightward |
| `right` | leftward |
| `top` | downward |
| `bottom` | upward |

Touching a boundary is insufficient when the arrowhead points outward or arrives along the boundary tangent.

Use an approach point outside the target, then make the final short segment perpendicular to the boundary. Apply the same principle at the source so a route does not appear to originate from another nearby node.

## Pre-render validation

Before the first render and after every geometry or connector revision, run:

```bash
python3 scripts/validate_svg.py <file-or-directory>
```

Treat these as hard failures:

- arrowed connector missing source or target metadata;
- declared source or target node does not exist;
- endpoint detached from the declared node boundary;
- side declaration does not match the endpoint;
- final segment approaches the target in the wrong direction;
- connector crosses the interior of an unrelated node;
- module or scope boundary crosses a node;
- unsupported path geometry prevents reliable endpoint validation.

The validator handles ordinary untransformed SVG nodes whose primary geometry is a `<rect>` and orthogonal `M`, `L`, `H`, and `V` connector paths. When using transforms, curves, polygons, or diamonds, either extend the deterministic validator or perform and record an equivalent bounding-box check. Do not silently downgrade an unvalidated route to “looks correct.”

## Semantic legibility after validation

Automated geometry cannot prove that a reader will understand the relationship. Inspect whether:

- a route passes behind or beside another node and appears to originate there;
- two edges share a segment that falsely implies a merged legal relationship;
- a label is closer to a different edge;
- parallel routes are too close to distinguish;
- an arrowhead is hidden by the target node or a module border;
- a cross-module edge can be mistaken for the module boundary;
- a relationship changes over time but the edge omits its effective or termination event.

Reroute, split the diagram, or add an explicit event／relationship hub when proximity would otherwise imply the wrong actor or destination.

## Mandatory enlarged connector crops

Create and inspect an enlarged crop for every connector cluster where:

- a node has two or more incoming or outgoing edges;
- a route crosses a lane or module;
- a polyline has three or more segments;
- solid and dashed lines meet or cross;
- labels sit near other paths;
- a path runs behind any node;
- several historical states or aliases appear in the same region.

Inspect the crop after the latest revision, not a previous render. Record any correction that changed an endpoint, route, label, module boundary, or node position.
