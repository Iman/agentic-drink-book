# Repository Guidelines

## Project Structure and Module Organization

`src/agentic_chat/` contains the Python application. Keep deterministic decisions in `policy.py`, ownership and retention in `context.py`, provider calls in `providers.py`, resilience in `resilience.py`, and graph orchestration in `workflow.py`. The CLI and evaluation harness have separate entry points.

`tests/` holds pytest checks. `features/` contains Behave Gherkin scenarios and Python steps. `docs/` contains architecture, security, validation and teaching notes; `docs/diagrams/` contains PlantUML sources and rendered assets. Bundled policy and evaluation data live alongside the package.

## Build, Test, and Development Commands

- `uv sync --locked`: install reproducible dependencies for Python 3.12 or 3.13.
- `uv run agentic-chat`: run the terminal chatbot with environment-provided credentials.
- `uv run pytest --color=no`: run deterministic tests.
- `uv run behave --no-color --format progress`: run Gherkin acceptance scenarios.
- `uv run agentic-eval`: run scripted regression evaluations; use `--suite holdout` for separate cases.
- `uv run ruff check src tests features scripts`: lint Python sources.
- `uv run ruff format --check src tests features scripts`: verify formatting.
- `uv build`: build the wheel and source distribution.

Live evaluation requires `--live`; it sends synthetic fixtures to the selected provider. See the README for local-model configuration and diagram commands.

## Coding Style and Naming

Use four-space indentation, type annotations at boundaries, `snake_case` functions/modules, and `PascalCase` classes. Ruff enforces formatting and lint rules. Reuse existing mechanisms before adding dependencies.

## Testing Guidelines

Name pytest files `test_*.py`. Write Gherkin scenarios in observable Given/When/Then terms. Cover rejected inputs, invalid judge evidence, context isolation, output gating, deadlines and concurrent circuit recovery. No coverage percentage is established. Keep expected evaluation labels independent of model outputs; distinguish scripted checks from live accuracy measurements.

## Security and Contributions

Treat all conversation and model content as untrusted. Only the host supplies identity and permissions. Never commit credentials or private conversations. Preserve failure handling and authorization checks.

There is no established Git history. Use concise imperative commit subjects. Pull requests should explain behavior, linked issues, tests and remaining limitations. Preserve existing hooks when integrating `scripts/check_commit_message.py`; do not add automated attribution. Keep changes within the approved design and update documentation with behavior changes.
