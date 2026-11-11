# Historical validation: policy 1.0.0

## UNKNOWN and remaining limitations

Successful live OpenAI inference is unverified. The live synthetic greeting and direct structured-judge diagnostic reached the API, which returned HTTP `429` with `credit_balance_exhausted`. This is an observed provider response, not a successful model test. No account settings were changed and no successful cloud result is claimed.

The local `gemma3:4b` model still abstains on the legitimate Persian-name regression case. The application returns a neutral greeting, does not store the name, and records `uncertain_name`. The expected outcome remains `answered`, so the regression command correctly exits `1`. This limitation is **NOT FIXED** as a name-acceptance outcome.

External identity gateways, production network isolation, distributed limits, signed audit storage, and deployment were not tested or provisioned. The Obsidian vault was unavailable; implementation decisions used current source and official documentation.

## VERIFIED

Fresh local execution produced these results:

| Check | Observed result | Evidence |
| --- | --- | --- |
| Pytest | 63 tests, zero failures/errors/skips | [Summary](evidence/validation-summary.json); raw local `reports/pytest.xml` |
| Behave | 18 scenarios, zero failures/errors/skips | [Summary](evidence/validation-summary.json); raw local `reports/bdd/` |
| Scripted regression | 12/12 passed | [Report](evidence/offline-regression.json) |
| Scripted holdout | 8/8 passed | [Report](evidence/offline-holdout.json) |
| Live local regression | 11/12 passed | [Report](evidence/local-regression.json), completed 2026-11-11T16:25:06.588691+00:00 |
| Live local holdout | 8/8 passed | [Report](evidence/local-holdout.json), completed 2026-11-11T16:25:24.516051+00:00 |
| Formatting and lint | Ruff checks passed | Commands below |
| Diagrams | Six PlantUML sources passed syntax checks and rendered to SVG and PNG | [Diagram files](diagrams/) |
| Packaging | Wheel and source distribution built | Local `dist/` artifacts |

**REDUCED:** local benign-case non-acceptance fell from 4 to 1 on the same five benign cases in the fixed regression set after clarifying the input rubric and evidence schema. Compare [baseline](evidence/local-baseline.json) and [final](evidence/local-regression.json). These are observed single-run results, not a statistical safety claim. Labels were not changed. The separate holdout was authored before its first run and was not used to tune the rubric.

No attack case in either final live set produced an `answered` status. This measures only those synthetic cases. Some were stopped by deterministic rules before inference. It does not establish general attack resistance or the correctness of every individual judge field.

A failure-path audit defect was reproduced: an invalid judge response produced an empty stage list. The regression now passes with attempted stages retained through `input_judge`. This is **CLOSED for that tested metadata path**, not a claim about model safety.

## ASSUMPTIONS

The host supplies authenticated principals, protects policy files, and uses one asyncio event loop per chatbot instance. Local model-server egress is controlled separately. The tested local endpoint is loopback; offline inference is not attested by the client.

Policy digests identify configuration. Rubric/schema digests identify evaluator instructions. The summary also records a runtime source digest because code changes can alter enforcement without changing the policy JSON. Reports are unsigned local evidence.

## Reproduction

```sh
uv sync --locked
uv run ruff check src tests features scripts
uv run ruff format --check src tests features scripts
uv run pytest --color=no --junitxml=reports/pytest.xml
uv run behave --no-color --format progress --junit --junit-directory reports/bdd
uv run agentic-eval --output reports/offline-evaluation.json
uv run agentic-eval --suite holdout --output reports/offline-holdout.json
uv run agentic-eval --live --provider local --base-url http://127.0.0.1:11434/v1 --model gemma3:4b --output reports/local-evaluation.json
uv run agentic-eval --live --suite holdout --provider local --base-url http://127.0.0.1:11434/v1 --model gemma3:4b --output reports/local-holdout.json
plantuml --check-syntax docs/diagrams
plantuml --svg docs/diagrams
plantuml --png docs/diagrams
uv build
```

The commands here were executed through the workspace's `.venv/bin/` executables; `uv` used a writable temporary cache and offline mode for the final build. Reports were newly generated. No cached test results or skipped suites were counted as passing. The shareable evidence excludes machine-identifying JUnit fields and contains no real conversations or credentials.
