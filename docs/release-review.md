# Release review: policy 2.0.0

This is the historical pre-publication review. See [multi-agent validation](multi-agent-validation.md) for policy 2.1.0 and the auditor extension.

What this change does: The repository provides a local drinks chatbot with English and Persian interfaces. This release adds bilingual setup documentation and records the security review before public publication.

## Must fix before relying on recipe accuracy

1. **The judge can approve an incorrect recipe.** See [output decisions](https://github.com/Iman/agentic-drink-book/blob/a10a9c1aef033b6d2cc08209989cb8b16e5210ab/src/agentic_chat/policy.py#L197) and [model selection](https://github.com/Iman/agentic-drink-book/blob/a10a9c1aef033b6d2cc08209989cb8b16e5210ab/src/agentic_chat/providers.py#L165).

   - **What this is:** The output judge supplies safety flags and quality scores. Application code uses these values to accept or reject the draft.
   - **Problem:** The recorded Persian Negroni case received an accepted answer but failed its ingredient check. Generation and judging used the same model.
   - **Fix:** Add reviewed recipe references and independent ingredient checks for named recipes. Rerun the failing fixture before claiming recipe accuracy.
   - **If we skip it:** Users can receive incorrect recipes after every gate passes. **NOT FIXED:** this release documents the failure without changing model behavior.

**VERIFIED historical evidence:** [The localization run](evidence/i18n/localization-live.json) recorded seven passes and one failure on 2026-11-11. At that review, source hashes matched [that validation summary](evidence/i18n/validation-summary.json). The review did not repeat live inference. Those hashes do not describe the later multi-agent refactor.

## VERIFIED checks

The [release evidence](evidence/release-review.json) records fresh results, commands, source hashes, and the limits of each check.

| Check | Result |
| --- | --- |
| Python tests | 87 passed, no failures or skips |
| Behave acceptance tests | 30 scenarios and 174 steps passed, no failures or skips |
| React DOM tests | Five passed, no failures or skips |
| Scripted evaluation | Regression 20/20, holdout 11/11, localization 8/8 |
| Python lint and format | Passed |
| Python and frontend builds | Completed |
| Python advisory scan | 63 locked registry packages checked, no known vulnerabilities reported |
| npm advisory scan | No known vulnerabilities reported |
| Persian Markdown | GitHub retained headings, lists, RTL alignment, and LTR code containers |

Source review followed browser input through HTTP checks, ownership, context loading, both judges, response release, and memory writes. Relevant tests cover origin and CSRF rejection, cross-session access, malformed judgments, output rejection, cancellation, and circuit recovery. Provider tests check credential separation, redirect rejection, and tracing suppression.

The public-file scan checked known credential patterns, available environment secrets, personal paths, addresses, and attribution markers. Its only credential-shaped match was the synthetic rejected URL in `tests/test_providers.py`. Local logs, environment files, IDE files, dependencies, and build artifacts are excluded from Git. This scan does not prove the absence of every possible secret.

The English and Persian READMEs now explain startup, model selection, language behavior, tests, and deployment limits. The existing contributor guide remains unchanged. The inherited commit hook retains its checks and also runs the repository guard.

## ASSUMPTIONS

The intended load is one local host process. This follows the launcher and loopback binding in `web.py`. Authenticated public traffic or multiple workers require a separate deployment design and shared state. Clearing browser cookies creates a new anonymous identity, so per-owner limits do not identify a person.

## UNKNOWN

This review did not perform a penetration test, sustained load test, browser visual test, or new live model evaluation. The DOM tests do not establish Persian font shaping or visual layout. Advisory results cover reported vulnerabilities at scan time. Model checks cannot establish immunity to prompt injection or social engineering.

The project memory vault was unavailable. Current source, fresh commands, and hash-checked historical evidence supplied the review evidence.

## ANSWER

Verdict: Ship. This verdict covers publication as a local teaching repository. Finding 1 remains open and blocks claims of reliable recipe accuracy. Public service deployment remains outside this release.

Not checked: live OpenAI inference, visual RTL rendering, sustained load, and adaptive attack resistance.
