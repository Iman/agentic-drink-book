# Security boundaries and remaining risks

## Application enforcement

The web host binds to `127.0.0.1:8000`. It checks Host and an explicit Origin set for localhost/127.0.0.1 on ports 8000 and 5173. An opaque HttpOnly SameSite cookie identifies a server-owned session; a separate token protects chat and reset requests against CSRF. Request bodies are bounded before JSON validation, extra fields are rejected, and client JSON cannot set principal, publisher role, policy or provider. Security headers restrict framing, scripts and caching. Model text is never inserted as HTML.

Cookies identify anonymous browsers, not verified people. Clearing cookies creates a new identity and can evade per-owner quotas; global concurrency and session capacity still apply. This local host is unsuitable for public traffic without authenticated identities and shared ingress limits. HTTP loopback cookies are not marked Secure; public deployment requires TLS and Secure cookies.

`ContextStore` requires the exact tenant and subject for session reads, writes and deletion. Shared documents require tenant agreement and explicit readership. Publishing requires a host-assigned publisher role. Model output cannot alter these values.

Policy schemas reject unknown fields and invalid types. Model evidence has no permission field. The graph fails closed on malformed evidence, uncertain judgments, provider failures, deadlines and output rejection. It releases no draft tokens before approval.

Known secret-shaped inputs are stopped before inference. Output rules reject terminal control sequences and known secret patterns. Local mode uses separate credentials and loopback destinations. The client disables environment proxy inheritance and redirects. Ambient LangSmith tracing is disabled around graph and model execution.

These controls are tested against explicit cases, not every possible input. `tests/` and `features/` identify their coverage.

## Threat and consequence coverage

| Threat | Control | Remaining limitation |
| --- | --- | --- |
| Cross-user disclosure | Host principal, exact session owner, explicit document audience | Forged host identity or a compromised process defeats this boundary. |
| Social engineering | Fixed policy, input evidence, code-owned permissions | Semantic detection is probabilistic. |
| Off-topic or mixed-topic requests | Drinks-only input relevance plus output `in_scope` checks | The model can falsely allow or falsely refuse topics; no universal topic-classification guarantee is claimed. |
| Prompt injection | Known patterns, context inspection, separate instructions/data, output inspection | Delimiters and a second model are not an injection-proof sandbox. |
| Memory poisoning | Screen ingestion, commit after output acceptance, bounded history, TTL | Accepted content remains untrusted and may contain undetected manipulation. |
| Offensive personalization | Canonicalized name checks and semantic inspection | Context, dialect and unfamiliar names can be misclassified. |
| Secret disclosure | Known-secret patterns, model checks, context isolation, minimal audit | Unknown secrets and personal data can reach the judge before semantic detection. |
| Provider failure or latency | Deadlines, bounded calls, circuit breaker, static fallback | Cancellation cannot undo provider processing or charges already incurred. |
| Traffic bursts | Per-owner rate, session busy flag, global and provider caps | Limits are not shared across processes. |
| Policy tampering | Immutable runtime policy and digest | Local files are not signed or protected against a privileged host attacker. |

## Context and data quality

Names are display preferences, not verified identities. Unsuitable names receive a neutral greeting and are not saved. Non-Latin letters are supported. Persian half-spaces (U+200C) are allowed only between Arabic-script letters. Other control/format characters, including bidirectional overrides, remain rejected. This deliberately does not support every Unicode joiner convention.

The response language is an allowlisted presentation setting. The HTTP header accepts only `en` and `fa`; unknown values fail before model calls. A fixed language instruction is selected in code. Changing the interface language neither translates stored history automatically nor changes session ownership, policy gates or document readership. Local storage contains the language code, not conversation text.

Documents have source labels, content digests, reader sets and expiry. Source labels are operator assertions. Neither a digest nor a judge establishes factual accuracy or source ownership. Context limits count characters, not exact tokens. Provider token output is separately capped.

Memory is in process. Expiry is enforced during store access, not by a background erasure service. `/reset` deletes the current session. These controls do not guarantee physical RAM erasure or govern provider retention.

## External controls

The terminal relies on the OS account; the web interface relies on a loopback browser-session boundary. Before exposing either publicly, supply authenticated identity mapping, TLS, ingress byte/time limits, distributed rate limits, secret management, isolation and outbound destination enforcement. The application body limit does not replace proxy-level connection or slow-client limits. Never derive `Principal`, publisher flags, policy paths or provider URLs from chat text.

Restrict model-server privileges and egress if local-only inference is required: a loopback server can itself proxy cloud requests. The client does not attest the server's behavior.

Public deployment needs policy ownership, review, incident escalation, retention, audit storage, monitoring and rollback. The metadata deque is bounded and process-local; it is not a durable, signed, tamper-evident trail. No such infrastructure is deployed here.

## Evaluation limits

The fixtures are a small regression set, not a safety benchmark. Scripted judgments do not measure detection accuracy. Live results do not establish protection against adaptive attacks, unseen languages or long conversations. Add independent labels and holdout cases; measure false positives and false negatives.

`minimum_quality` is an uncalibrated threshold over model scores. Treat it as a teaching mechanism until compared with human labels. Do not present the application as immune to hijacking.
