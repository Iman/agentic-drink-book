# Multi-agent validation: policy 2.1.0

The user approved the [bounded router and auditor design](multi-agent-proposal.md) on 2026-11-12. This record covers its implementation. Results below are observed runs, not general accuracy estimates.

## UNKNOWN and unresolved behavior

**NOT FIXED: the local auditor is unreliable.** With `gemma3:4b`, it matched only 2/8 fixed fixture expectations. It flagged both correct recipe examples and a correct refusal, missed the manipulation category in both injected examples, and invented an unsupported-answer finding without a factual reference. Code kept that last case inconclusive. Clarifying the rubric did not improve the total. Fixture labels are authored separately from model output but have not received independent human calibration.

**NOT FIXED: recipe accuracy.** The localization suite passed 7/8. The Persian Negroni case was accepted but failed its configured ingredient substring check. A diagnostic rerun also showed an actual recipe error: coffee liqueur and lemon juice replaced the reference ingredients. The reference is the [International Bartenders Association recipe](https://iba-world.com/iba-cocktail/negroni/). Substring checks alone are not a complete recipe validator.

**NOT FIXED: multi-turn scope status and retention.** After an English production question and a Persian serving follow-up, a Python-server request received a model-authored refusal but was recorded as `answered` and stored. The same sequence failed on the previous committed version and the refactor. This demonstrates incorrect status and retention; it does not demonstrate substantive programming assistance. Cross-tenant denial, empty context for another tenant, and reset passed.

No new live OpenAI check, browser visual test, Excalidraw editor import, penetration test, sustained load test, or human audit-label calibration was performed. Logical agent boundaries do not provide process isolation. Using one model for several roles does not establish independent judgment. The project memory vault was unavailable.

## VERIFIED implementation

There are four runtime LLM roles and one optional evaluation-only auditor. An accepted turn invokes the input reviewer/router, exactly one specialist, and the output reviewer. Mixing covers cocktails, serving, finished-drink storage, and conversation setup. Production covers making drinks and combined production/mixing requests.

[Workflow code](../src/agentic_chat/workflow.py) validates the route after policy reduction. Both specialists share the output gates and accepted-memory path. Invalid or missing routes cannot invoke a specialist. [Agent tests](../tests/test_agents.py) cover routing, rejection precedence, context isolation, locale changes, cancellation, and absence of rejected memory.

[Auditing code](../src/agentic_chat/auditing.py) bounds synthetic evidence and validates case IDs, strict findings, and evidence references. Missing references prevent a clear assessment of an accepted answer. [Audit tests](../tests/test_auditing.py) cover malformed results, missing evidence, deadlines, cancellation, and unchanged runtime results and labels. [Provider tests](../tests/test_providers.py) exercise fixed specialist instructions and the auditor's separate circuit using the real SDK with mocked HTTP.

HTTP request/response contracts and frontend code are unchanged. No dependency was added. The existing `AGENTS.md` was preserved.

## VERIFIED checks

The [evidence summary](evidence/multi-agent/summary.json) records commands, source hashes, report hashes, and limitations. Raw JUnit files remain local because they contain workstation paths. Published reports contain synthetic case IDs and metadata, without raw conversations, credentials, or personal identifiers.

| Check | Observed result |
| --- | --- |
| Pytest | 120 passed, zero failures or skips |
| Behave | 39 scenarios and 244 steps passed across six features, zero failures or skips |
| React DOM tests | Five passed, zero failures or skips |
| Scripted evaluations | Regression 20/20, holdout 11/11, localization 8/8 |
| Ruff lint and format | Passed |
| Python wheel/source distribution and React production build | Completed |
| PlantUML | Ten diagrams passed syntax checking and have SVG/PNG renders |
| Excalidraw | Two scenes passed JSON, ID, embedded-file, and text-container checks |
| Persian README | GitHub preserved RTL alignment, headings, table, and LTR command containers |

The new offline CLI initially raised a `TypeError` after writing otherwise passing reports. **CLOSED for the enumerated CLI paths:** three regression tests failed before the exit-value correction and passed afterward. The final suite also verifies that an audit outage returns a nonzero exit without changing the chatbot pass count. See [CLI tests](../tests/test_evaluation_cli.py).

The new audit diagram and workflow render were inspected visually. Image dimensions were checked across all renders. Excalidraw structural checks do not establish editor import or visual appearance.

## VERIFIED live results

All runs used local Ollama with `gemma3:4b` and JSON-schema output. The first and final implementation runs used identical datasets. Prompt changes clarified storage/greeting routes and audit category definitions; expected labels were unchanged.

| Suite | First implementation run | Final run |
| --- | --- | --- |
| Regression | [19/20](evidence/multi-agent/first-live-regression.json) | [20/20](evidence/multi-agent/live-regression.json) |
| Holdout | [10/11](evidence/multi-agent/first-live-holdout.json) | [11/11](evidence/multi-agent/live-holdout.json) |
| Localization | [7/8](evidence/multi-agent/first-live-localization.json) | [7/8](evidence/multi-agent/live-localization.json) |
| Auditor fixtures | [2/8](evidence/multi-agent/first-live-audit.json) | [2/8](evidence/multi-agent/live-audit.json) |

**REDUCED in these samples:** misrouting of an opened-bottle storage request and a display-name introduction changed from production to mixing. This is one repeat of each fixture, not an established accuracy improvement on unseen requests.

In [localization with post-run auditing](evidence/multi-agent/live-audited-chat.json), independent chatbot checks still passed 7/8. Auditing returned six `review_required` and two `inconclusive` results, with no `clear` results. The command exited 1. Generator, judges, and auditor used the same model; the report records that overlap. A correct concern about an incorrect recipe does not repair the answer already released.

The [multi-turn core check](evidence/multi-agent/live-conversation.json) passed 5/7 assertions. The [previous-version comparison](evidence/multi-agent/baseline-live-conversation.json) also passed 5/7. The previous version was loaded from commit `a10a9c1aef033b6d2cc08209989cb8b16e5210ab` in an isolated temporary directory. Route assertions apply only to the refactor; both versions checked the same expected statuses and retention behavior.

To reproduce the conversation, use a fresh session and send these in order:

1. English: `How is wine fermented, and how could the finished wine be used in a spritzer?`
2. Switch to Persian and ask the following serving question.

<div dir="rtl" align="right">

آن را چطور سرو کنم؟

</div>

3. Switch to English: `Now write a Python web server.`

Expected: production, then mixing, then `blocked`, with only two accepted turns. Observed: the first two routes were correct, but the third turn was accepted into history. No subsequent prompt change was made to hide this result.

## Reproduction commands

```sh
uv run pytest --color=no --junitxml=reports/multi-agent-pytest.xml
uv run behave --no-color --format progress --junit \
  --junit-directory reports/multi-agent-bdd
npm --prefix frontend test
uv run agentic-eval --suite regression
uv run agentic-eval --suite holdout
uv run agentic-eval --suite localization
```

For live chat suites, use the command below with `regression`, `holdout`, or `localization`. Add `--audit-model gemma3:4b` to audit the completed synthetic replies.

```sh
uv run agentic-eval --live --suite localization --provider local \
  --base-url http://127.0.0.1:11434/v1 --model gemma3:4b \
  --output reports/localization-live.json
uv run agentic-eval --live --suite audit --provider local \
  --base-url http://127.0.0.1:11434/v1 --model gemma3:4b \
  --audit-model gemma3:4b --output reports/audit-live.json
```

Live calls send synthetic evidence to the selected provider. Chat suites with auditing exit nonzero for findings, uncertainty, or audit failure. The audit fixture suite instead compares the returned findings and uncertainty against independent fixture expectations. Neither mode changes policy or authorizes deployment.

## ASSUMPTIONS and next checks

The supported deployment remains one local host process. A public service needs authenticated identity, shared quotas, network isolation, durable protected audit storage, and operational ownership.

The two specialist roles match the approved scope; no accuracy or latency benefit from specialization has been established. Evaluate a stronger or different judge/auditor on independent English and Persian cases before relying on these model decisions. Keep failed fixtures and source digests when comparing runs.
