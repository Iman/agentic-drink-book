# Validation record: drinks chatbot, policy 2.0.0

For policy 2.1.0, see [multi-agent validation](multi-agent-validation.md).

This page records the drinks UI baseline before localization. For the later English/Persian
change, see [language implementation and validation](localization.md). Each evidence set has
its own source and prompt digests; the counts below are historical, not the latest suite totals.

## UNKNOWN and limits

Browser automation was unavailable. The React production build and HTTP integration were checked, but visual layout, keyboard interaction and mobile rendering were not verified in a browser. Excalidraw files passed structural and text-bound checks; interactive editor import remains unverified.

OpenAI inference was not retested in this extension. Earlier API quota failures and policy-1.0.0 results are preserved in the [historical record](validation-policy-1.md). No public deployment, verified account identity, distributed quotas or network isolation was provisioned. The Obsidian vault was unavailable.

The live fixtures are small synthetic samples. They do not establish immunity to social engineering, factual accuracy of all recipes, or safe operation of alcohol-production equipment. Judges and generation used the same local model.

## VERIFIED

Fresh results from this extension are recorded in the [validation summary](evidence/cocktail-v2/validation-summary.json), including source hashes, policy digest and rubric/schema digest.

| Check | Observed result | Evidence |
| --- | --- | --- |
| Python tests | 72 passed, zero failures/errors/skips | Summary; local `reports/pytest-web.xml` |
| Behave BDD | 26 scenarios and 142 steps passed; zero skipped | Summary; local `reports/bdd-web/` |
| Scripted regression | 20/20 passed | [Report](evidence/cocktail-v2/offline-regression.json) |
| Scripted holdout | 11/11 passed | [Report](evidence/cocktail-v2/offline-holdout.json) |
| Live Ollama regression | 20/20 passed | [Report](evidence/cocktail-v2/live-regression.json) |
| Live Ollama holdout | 11/11 passed | [Report](evidence/cocktail-v2/live-holdout.json) |
| Live HTTP chat | 5/5 expected outcomes; two accepted turns retained; reset and CSRF rotation passed | [Report](evidence/cocktail-v2/web-live.json) |
| React | Production build completed; built page served through FastAPI | Build output and live HTTP report |
| Python tooling | Ruff lint/format passed; wheel and source distribution built | Commands below |
| Diagrams | Nine PlantUML sources checked and rendered; two Excalidraw scenes structurally checked | [Catalogue](diagrams/README.md) |

Live HTTP cases covered a Negroni, a context-dependent follow-up, an unrelated coding request, a mixed request and an offensive display name. No off-topic request in the live regression or holdout was answered. This statement is limited to those observed cases.

## Before and after

**REDUCED:** expected drink answers refused by the local judge fell from 8/10 to 0/10 across runs with identical regression dataset digests. The [baseline](evidence/cocktail-v2/live-baseline.json) passed 12/20 overall; the [intermediate run](evidence/cocktail-v2/live-intermediate.json) passed 18/20; the [final run](evidence/cocktail-v2/live-regression.json) passed 20/20. Runtime source and rubric changes distinguish these runs. This is a single-run comparison, not a confidence estimate or isolated performance benchmark.

Direct inspection found an ordinary recipe flagged as following injected instructions and a qualified storage answer flagged as judge uncertainty. Schema descriptions and rubrics now distinguish recipe instructions from policy overrides, and answer caveats from the judge's inability to assess evidence. Safety flags, uncertainty rejection and quality thresholds remain enforced. The holdout was run after these clarifications and was not used for this tuning.

**CLOSED for the tested deterministic paths:** an off-topic input with an uncertain name now produces `out_of_scope`, and an off-topic draft with high scores is discarded before release or memory commit. Both regression tests were observed failing before the change and passing afterward. See `tests/test_drinks_scope.py`. This verdict does not extend to model classification accuracy.

Policy 2.0.0 intentionally changes general-question expectations from the earlier policy. Historical policy-1.0.0 datasets and results must not be treated as the same benchmark. `benign_cases_blocked` includes harmless but deliberately out-of-scope requests; use `expected_answer_cases_not_answered` for unexpected non-acceptance.

## Reproduction

Run from the repository root with Ollama and `gemma3:4b` available:

```sh
uv sync --locked
uv run ruff check src tests features scripts
uv run ruff format --check src tests features scripts
uv run pytest --color=no --junitxml=reports/pytest-web.xml
uv run behave --no-color --format progress --junit --junit-directory reports/bdd-web
uv run agentic-eval --output reports/cocktail-offline.json
uv run agentic-eval --suite holdout --output reports/cocktail-holdout.json
uv run agentic-eval --live --provider local --base-url http://127.0.0.1:11434/v1 --model gemma3:4b --output reports/cocktail-live-final.json
uv run agentic-eval --live --suite holdout --provider local --base-url http://127.0.0.1:11434/v1 --model gemma3:4b --output reports/cocktail-live-holdout.json
npm --prefix frontend ci
npm --prefix frontend run build
uv build
./scripts/start.sh
```

Python checks were executed using the installed `.venv/bin/` commands; uv used a writable temporary cache. Test results were fresh, with nonzero counts. Shareable reports contain outcome metadata and synthetic case IDs. Machine-identifying JUnit fields, credentials and real conversations are excluded. The current Python wheel contains the backend; the web entry point expects the built `frontend/dist` directory in the repository working directory.
