# English and Persian

This records the earlier localization change. See [multi-agent validation](multi-agent-validation.md) for current routing, audit, and test results.

## Use the language selector

Open the local web app and choose English or Persian from the Language selector above the
conversation. The selected language applies to controls, starter questions, status messages,
errors, static refusals and subsequent model replies. Existing messages and drafts are
preserved. Switching is disabled while a request is pending.

The browser saves only `en` or `fa` under `drinks-language` in local storage. A saved choice
takes priority over the browser language. On first use, a Persian browser locale selects
Persian; other locales use English. Storage failures do not prevent in-memory switching.

## Layout and text

The React catalog is `frontend/src/i18n.js`. The document and app set `lang` and `dir`, and
CSS uses logical borders, margins and alignment to mirror the layout. Persian removes the
English display font's negative letter spacing and uses Tahoma with system fallbacks.
Numerals use `Intl.NumberFormat` for the selected locale.

Messages and the textarea use `dir="auto"`; message text also uses `unicode-bidi: plaintext`.
Latin keyboard shortcuts and numeric counters use isolated left-to-right spans. Model output
is still rendered as plain text. See the platform documentation for
[text direction](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Global_attributes/dir)
and [logical CSS properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Logical_properties_and_values).

## API and safety

Every browser request sends `X-Chat-Language: en` or `X-Chat-Language: fa`. The API rejects
unknown values before inference and defaults to English when the header is absent. Request
JSON still permits only `message`; identity and policy remain server-owned.

`localization.py` provides server translations and fixed language instructions. The language
preference reaches LangGraph through trusted runtime context. LangChain selects a fixed
instruction by exact language code. Persian replies begin with the configured Persian
greeting. Judges assess both languages under the same scope and safety rules.

Persian half-spaces (U+200C) pass input and output screening only when immediately surrounded
by Arabic-script letters. Bidirectional overrides, isolates and half-spaces inserted into
Latin words remain blocked. No general exception for invisible characters was introduced.

The output judge checks the current request's scope as well as the draft. A polite refusal
to an unrelated request must not become an accepted conversation turn. Earlier drink history
cannot make a programming request relevant. Model observations remain fallible.

## Tests and reproduction

```sh
npm --prefix frontend test
npm --prefix frontend run build
uv run pytest --color=no
uv run behave --no-color --format progress
uv run agentic-eval --suite localization
uv run agentic-eval --suite localization --live --provider local \
  --base-url http://127.0.0.1:11434/v1 --model gemma3:4b
uv run agentic-chat --language fa --provider local \
  --base-url http://127.0.0.1:11434/v1 --model gemma3:4b
```

The React tests mount the actual component in jsdom. They check language switching, saved
preferences, storage failure, draft preservation, translated errors, direction attributes
and outgoing language headers. Python tests cover localized replies/errors, locale rejection,
half-spaces, blocked controls, fixed provider instructions and conversation retention.
Behave scenarios exercise both reply languages using scripted model evidence.

Browser automation was unavailable during this change. DOM tests do not verify font shaping,
visual alignment or mobile rendering in a real browser. Native-speaker review and broader
multilingual adversarial evaluation remain necessary before treating translation quality or
safety accuracy as established. The local model can misinterpret Persian loanwords; starter
prompts include the Latin name of Negroni to reduce that ambiguity.

## Validation outcome

**NOT FIXED:** the tested local `gemma3:4b` model produced an incorrect Persian Negroni
recipe, and its output judge accepted it. Bilingual naming reduced the initial confusion
with the Persian word for worry, but did not establish ingredient accuracy. The stricter
localization regression passed 7/8 cases; the failed case remains visible. The earlier
baseline checked reply status and greeting only, so its 8/8 result is not comparable to the
strengthened recipe-content assertion.

**VERIFIED:** 87 Python tests, 30 Behave scenarios and five React DOM tests passed. The
scripted localization suite passed 8/8 and the final live English regression passed 20/20.
The live HTTP conversation returned the selected language on all four turns; its recipe
ingredient assertion failed, giving 3/4 overall. Invalid locale rejection, Persian validation
errors, history preservation across language changes and reset passed.

**REDUCED in the observed conversation:** an unrelated request after a Persian-to-English
language switch initially received a model-authored refusal but was recorded as an accepted
turn. After clarifying that output scope includes the current request, the repeated sequence
returned `blocked` and retained only the two accepted drink turns. This is one observed live
sequence, not proof that the model will always classify refusals correctly.

The [validation summary](evidence/i18n/validation-summary.json) records fresh counts and source
hashes. See the [localization live report](evidence/i18n/localization-live.json),
[English live report](evidence/i18n/english-live.json) and
[HTTP report](evidence/i18n/web-live.json). Reports contain outcome metadata and synthetic case
IDs, without private conversations or credentials. No new live OpenAI check was performed.
