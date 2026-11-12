# Architecture diagrams

Thirteen PlantUML sources have SVG and PNG renders. Two editable Excalidraw scenes cover the
functional flow and trust boundaries. The set describes the implemented React/FastAPI path,
bounded specialist routing, runtime judges, and optional evaluation-only auditor.

Start with [L0 system context](13-l0-system-context.svg), [L1 components](14-l1-runtime-components.svg),
and the [functional view](15-functional-flow.svg). L0 and L1 are this repository's view labels:
L0 shows people and external systems; L1 expands application components and logical boundaries.
The functional view follows a request through review, release, refusal, and retention.

Download [the offline HTML catalogue](index.html) and open it locally to browse every rendered
view without a server or internet connection. SVGs remain embedded in that file. GitHub shows
HTML as source; use the individual SVG/PNG links when reading online.

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
| [12 Audit governance](12-audit-governance.svg) | Runtime authority, synthetic evidence, advisory findings, and human review |
| [13 L0 system context](13-l0-system-context.svg) | Learner, operator, application, provider choice, and external deployment requirements |
| [14 L1 components](14-l1-runtime-components.svg) | Browser, Python entry points, host authority, context, provider circuits, and evaluation |
| [15 Functional view](15-functional-flow.svg) | Request, review, specialist selection, release, refusal, and memory behavior |

Open the `.excalidraw` files with Excalidraw's **Open** command. They contain editable shapes,
labels and arrows, without embedded images or private conversation data. Both include a
separate synthetic-evaluation row for the auditor and human review. Their format follows
the [documented Excalidraw JSON schema](https://plus.excalidraw.com/docs/sdk/codebase/json-schema).
They were created locally because no Excalidraw connector was available. Structural checks
were run; interactive editor import was not verified in this session.

Regenerate SVGs, PNGs, and the offline HTML catalogue from the repository root. Install
PlantUML and `rsvg-convert` first; the script uses only Python's standard library.

```sh
python3 scripts/render_diagrams.py
```

The renderer checks PlantUML syntax, parses each SVG, adds accessible titles/descriptions,
prefixes IDs for the combined HTML file, and checks PNG/SVG proportions. PNGs are exported
from SVG so large sequence diagrams keep their bounds. Edit `.puml` sources rather than
rendered files. Edit `.excalidraw` files in Excalidraw; the renderer does not convert those scenes.

The detailed sequence now stops before the output judge when output rules reject a draft,
and shows reset returning a conflict for an active turn. Context diagrams identify the
host's commit function as the only memory writer. [Publication checks](../publication-review.md)
record the validation and known limitations of this diagram set.

Boundary boxes identify trust and ownership responsibilities. The safety net and schema
reducers share one Python process. The specialists, input and output judges, and optional auditor are logical roles and may use
the same model. These boxes do not imply hardware isolation, independent
judgment, or guaranteed resistance to social engineering.
