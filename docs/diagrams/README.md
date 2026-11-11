# Architecture diagrams

PlantUML sources, SVG and PNG renders are stored together. The new web set describes the
implemented local React/FastAPI path; the earlier graph and circuit diagrams remain useful
for the Python core.

| Diagram | Teaching purpose |
| --- | --- |
| [01 System](01-system.svg) | CLI, browser, host, provider and external deployment controls |
| [02 Core sequence](02-turn-sequence.svg) | Input inspection through output release and memory commit |
| [03 Workflow](03-workflow.svg) | Acyclic LangGraph routes and stop conditions |
| [04 Circuit breaker](04-circuit-breaker.svg) | Closed, open, half-open, deadlines and stale completions |
| [05 Context](05-context.svg) | Ownership, document readers, retention and admission |
| [06 Governance](06-governance-evaluation.svg) | Evaluation evidence and release responsibilities |
| [07 Web boundaries](07-web-boundaries.svg) | Browser, HTTP, safety net, judge contract and model service |
| [08 Judge and safety net](08-judge-safety-boundary.svg) | Model observations versus application authority |
| [09 Web sequence](09-web-sequence.svg) | Cookie/CSRF setup, request flow, refusals and reset |
| [10 Functional flow](10-functional-flow.excalidraw) | Editable hand-drawn overview for teaching |
| [11 Trust boundaries](11-trust-boundaries.excalidraw) | Editable hand-drawn responsibility map |

Open the `.excalidraw` files with Excalidraw's **Open** command. They contain editable shapes,
labels and arrows, without embedded images or private conversation data. Their format follows
the [documented Excalidraw JSON schema](https://plus.excalidraw.com/docs/sdk/codebase/json-schema).
They were created locally because no Excalidraw connector was available. Structural checks
were run; interactive editor import was not verified in this session.

Render the PlantUML set from the repository root:

```sh
plantuml --check-syntax docs/diagrams
plantuml --svg docs/diagrams
plantuml --png docs/diagrams
# Optional: export the sequence PNG directly from the SVG to preserve its bounds.
rsvg-convert docs/diagrams/09-web-sequence.svg --background-color white \
  --output docs/diagrams/09-web-sequence.png
```

Boundary boxes identify trust and ownership responsibilities. The safety net and schema
reducers share one Python process. Input and output judges are logical roles and may use
the same model as generation. These boxes do not imply hardware isolation, independent
judgment, or guaranteed resistance to social engineering.
