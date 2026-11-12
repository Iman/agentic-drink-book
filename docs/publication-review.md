# Publication review: multi-agent implementation and diagram set

This review covers the approved multi-agent implementation plus the requested L0, L1,
functional, and detailed diagram updates. The application behavior and fixtures match the
[recorded multi-agent live runs](multi-agent-validation.md); their source hashes were checked
again before publication. No new live inference result is claimed here.

## UNKNOWN and remaining risks

The earlier live failures remain open: the local auditor matched 2/8 fixture expectations,
the Persian Negroni answer was incorrect, and a multi-turn programming refusal entered
accepted history. Publication of the source does not resolve those model failures or make
the local service suitable for public traffic.

The HTML catalogue passed structural checks, but was not visually tested in a browser.
Excalidraw scenes passed JSON and element checks; interactive editor import was not tested.
No new live OpenAI, sustained-load, or penetration test was run. The project memory vault
was unavailable.

## VERIFIED changes

- L0 shows the learner, operator, application, provider choice, and external deployment needs.
- L1 shows entry points, code-owned policy/context, the graph, provider circuits, and evaluation.
- The functional view follows input review, one specialist, output review, and release or fallback.
- Detailed diagrams show host-owned memory writes, rejection before model calls, output-rule
  rejection before the output judge, and reset conflict while a turn is active.
- All 13 PlantUML diagrams have fresh SVG/PNG renders. The offline HTML file embeds those
  SVGs, adds navigation, and uses unique IDs with accessible titles and descriptions.
- Both editable Excalidraw scenes and both READMEs link the new views. `AGENTS.md` is unchanged.

The L0, L1, functional, context, and web sequence renders were inspected. Detailed boundaries
remain logical responsibilities within the application, not separate security sandboxes.
The existing PlantUML/Excalidraw formats and component vocabulary were retained. L0 and L1
collapse detailed judge fields and circuit transitions into components; diagrams 04, 08,
and 12 retain those details. No runtime subsystem was added by drawing these views.

## VERIFIED checks

| Check | Result |
| --- | --- |
| Pytest | 120 passed, zero failures or skips |
| Behave | 39 scenarios and 244 steps across six features, zero failures or skips |
| React DOM tests | Five passed, zero failures or skips |
| Scripted evaluation | Regression 20/20, holdout 11/11, localization 8/8 |
| Python lint and formatting | Passed |
| Python and React builds | Completed |
| PlantUML and rendered assets | 13 syntax checks and SVG/PNG dimension checks passed |
| Editable scenes | Two JSON scenes, 46 uniquely identified elements each |
| Offline HTML | 13 embedded SVGs, unique IDs, no scripts or external display assets |
| Persian README | GitHub preserved RTL layout, headings, table, and LTR command blocks |

Commands, source hashes, and the scope of the file scan are recorded in
[publication evidence](evidence/publication-review.json). Historical live reports and their
original source hashes remain in `docs/evidence/multi-agent/`. The updated diagrams have
separate hashes in this publication record. Raw logs remain in the ignored `reports/` directory.

Regenerate diagrams with `python3 scripts/render_diagrams.py`. See the
[diagram catalogue](diagrams/README.md) for individual views and the offline viewer.
