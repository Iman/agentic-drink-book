# Architecture and selected patterns

## Scope and trust

The executable surfaces are a Python terminal and a local React/FastAPI app. The host creates a `Principal`; conversation content cannot choose its tenant, subject or publisher role. FastAPI maps an opaque HttpOnly browser cookie to a server-created principal and conversation. This isolates anonymous browser sessions; it does not authenticate people. Public deployment requires verified identity mapping before invoking `Chatbot.chat`.

Policy 2.0.0 restricts substantive requests and answers to drinks. Cocktails, fermentation, wine, beer, whiskey and Persian Arak Sagi production are included. Brief greetings and display-name setup may redirect to drinks. Mixed-topic requests and topic changes disguised with drink vocabulary are rejected when detected. Semantic scope detection remains model-dependent.

The [web boundary diagram](diagrams/07-web-boundaries.svg), [judge contract diagram](diagrams/08-judge-safety-boundary.svg) and [web sequence](diagrams/09-web-sequence.svg) separate HTTP controls, deterministic policy, logical judge roles and the model service. The [diagram catalogue](diagrams/README.md) includes editable Excalidraw scenes for teaching.

The workflow is acyclic. There are no tools, browser actions, shell execution, automatic retries or self-modifying policies. See [the system diagram](diagrams/01-system.svg), [sequence](diagrams/02-turn-sequence.svg) and [graph](diagrams/03-workflow.svg).

## Pattern selection

The [Agentic Patterns catalogue](https://www.agentic-patterns.com/) is a reference, not evidence that this application is secure. These patterns fit the actual failure paths:

| Reference | Implementation | Qualification |
| --- | --- | --- |
| [Agent Circuit Breaker](https://www.agentic-patterns.com/patterns/agent-circuit-breaker) | `resilience.py`: closed/open/half-open, one probe, monotonic cooldown, deadlines, stale-completion protection | Separate generation and judge circuits. Busy admission is not a provider failure. |
| [Evidence Questions, Not Verdict Questions](https://www.agentic-patterns.com/patterns/evidence-questions-not-verdict-questions) | `InputEvidence`, `OutputEvidence` and policy reducers | Models report observations; code selects outcomes. Incorrect observations can still produce incorrect outcomes. |
| [Versioned Constitution Governance](https://www.agentic-patterns.com/patterns/versioned-constitution-governance) | Frozen startup policy, validated fields, effective-policy digest in results and evaluations | Signed reviews, protected branches, canaries and rollback remain deployment procedures. |
| [Workflow Evals with Mocked Tools](https://www.agentic-patterns.com/patterns/workflow-evals-with-mocked-tools) | Scripted evidence drives the real graph in pytest, Behave and offline evaluation | Tests prove enforcement with given evidence. Live inference is evaluated separately. |

LangChain's [guardrail documentation](https://docs.langchain.com/oss/python/langchain/guardrails) describes complementary deterministic and model-based checks. Here they are explicit LangGraph nodes so stop conditions and memory writes can be tested.

## Data path

| Source | Responsibility | Regression checks |
| --- | --- | --- |
| [workflow.py](../src/agentic_chat/workflow.py) | Graph, response release, metadata audit | [Workflow tests](../tests/test_workflow.py) |
| [context.py](../src/agentic_chat/context.py) | Ownership, readership, bounded memory, admission | [Context scenarios](../features/context_isolation.feature) |
| [policy.py](../src/agentic_chat/policy.py) | Schemas and deterministic reductions | [Policy tests](../tests/test_policy.py) |
| [providers.py](../src/agentic_chat/providers.py) | Credentials, rubrics, structured inference | [Provider wire-contract tests](../tests/test_providers.py) |
| [resilience.py](../src/agentic_chat/resilience.py) | Deadlines, capacity and breaker states | [Resilience tests](../tests/test_resilience.py) |
| [evaluation.py](../src/agentic_chat/evaluation.py) | Independent expectations and reports | [Governance tests](../tests/test_governance.py) |
| [web.py](../src/agentic_chat/web.py) | Host/origin checks, cookie identity, CSRF, bounded JSON and HTTP status mapping | [Web tests](../tests/test_web.py) |
| [React interface](../frontend/src/main.jsx) | Starters, buffered plain-text replies, reset and errors | Build verified; visual browser verification unavailable |

1. `ContextStore.admit` checks owner, expiry, per-owner rate and concurrent use. `Chatbot` enforces the global in-flight cap.
2. `input_rules` checks size, control characters, known secret patterns, obvious instruction overrides and configured insulting names.
3. `load_context` retrieves authorized, unexpired records within a character budget.
4. `input_judge` receives the current message and context as untrusted JSON. Schema validation and deterministic reduction select the route. `relevant=false` rejects unrelated or mixed-topic requests before generation.
5. `generate` creates a buffered draft. History and documents remain user-message data, never system instructions.
6. `output_rules` and `output_judge` inspect the exact draft. Safety, `in_scope`, uncertainty, relevance and groundedness determine release. Scope includes the current request, even when the draft politely refuses it, so rejected requests are excluded from accepted history. High quality scores cannot override a false `in_scope` observation.
7. `commit` rechecks ownership and retains only the accepted exchange. Rejected inputs and drafts never enter conversation memory.

This uses the documented [LangGraph state and edge API](https://docs.langchain.com/oss/python/langgraph/graph-api). Raw graph checkpoints are disabled because they could retain rejected input and drafts. [Context lifecycle](diagrams/05-context.svg) shows the separate application store.

## Reliability and traffic

The policy defaults allow 20 requests per owner per minute, four concurrent turns globally, and one active turn per session. Each role's provider circuit also caps concurrency. There is no unbounded waiting queue.

Each call has a 20-second deadline. Completed calls exceeding 15 seconds are discarded and counted as failures. Three consecutive failures open that role's circuit for 30 seconds. The first eligible call afterward is the sole recovery probe. A whole turn has three call budgets plus one second.

These are defaults in `policy.json`, not benchmark-derived service targets. See [the breaker diagram](diagrams/04-circuit-breaker.svg). All limits are process-local and assume one asyncio event loop per chatbot instance. A distributed service needs shared limits and deployment-level load shedding.

## Governance and evaluation

The [governance diagram](diagrams/06-governance-evaluation.svg) separates executable checks from release procedures. Policy or rubric changes should run offline tests, then live synthetic cases and independently authored holdouts. Keep failed cases visible.

Online judge scores are not the evaluation oracle. `eval_cases.json` and `eval_holdout.json` hold independent expected outcomes and response constraints. Reports record policy, rubric/schema and dataset digests, live model selection, completion time, outcomes and latency percentiles. Provider failures remain failures.

Generation and judge models can differ through `--judge-model` but share the selected provider. The default uses the same model, so correlated errors remain a risk. There is no claim of independent adjudication or calibrated confidence.

## Web lifecycle

`POST /api/session` checks Origin and creates or restores a cookie session, returning a CSRF token and accepted history. `POST /api/chat` requires that cookie and token, permits only a `message` field and reads at most 32,768 body bytes before parsing. The optional `X-Chat-Language` header accepts only `en` or `fa`, defaults to English, and controls presentation without changing authorization. A fixed server-owned language instruction reaches the response model; the output judge still inspects the exact draft. `POST /api/reset` rotates the conversation and CSRF token while retaining the owner and its recent rate history. Reset is refused while a turn is busy.

Refusals and accepted replies use HTTP 200 with separate status fields. Busy/rate denial uses 429, provider failure uses 503, and an expired session uses 401. The UI retains failed request text for retry and renders answers as text, without interpreting model HTML. Response headers restrict scripts, framing and caching.

`scripts/start.sh` builds the UI and runs one Uvicorn process on port 8000. It starts a loopback Ollama service only if one is not already responding, checks the installed model and cleans up its own children on exit. The same FastAPI process serves built static assets. State and limits are deliberately process-local.
