# Endosoma-friendly — design canon

Locked for this change. Read after compact. Do not re-ask locked rows.
Open questions stay open until the designer answers.

Hunt identity and loss **rules** remain in
`openspec/changes/archive/2026-09-04-velociraptor-hunt/DESIGN_CANON.md`
and `openspec/changes/archive/2026-09-12-hunt-deferred/DESIGN_CANON.md`.
This file only covers the **post-swallow stance** and Options hiding.

---

## Locked

| # | Decision | Locked |
|---|----------|--------|
| E1 | Options row **Post-swallow** with **Digest** and **Endosoma**. | 2026-09-14 |
| E2 | **Digest is the default.** Missing/invalid settings key → Digest. | 2026-09-14 |
| E3 | Digest selected: **no change** to current loss copy, Stats label, GAME OVER second line, swallow-angle lines, or belly darkening. | 2026-09-14 |
| E4 | Endosoma is still a **game over**. No escape, no continue-from-belly, no second ending. | 2026-09-14 |
| E5 | Endosoma **Stats** wording: **Times swallowed** instead of **Times digested**. Same persisted counter (`digested` in JSON). | 2026-09-14 |
| E6 | Endosoma **GAME OVER** second line (placeholder): **The raptor got you.** Title stays **GAME OVER** (same as other endings). | 2026-09-14 |
| E7 | Narratives are **data-driven path pools** so new stories can be added in JSON without code. | 2026-09-14 |
| E8 | Endosoma tone: raptor **flaunts capture/containment** and struts; hunter is chagrined; colleagues will laugh for ages. Whimsy, not digestion horror. | 2026-09-14 |
| E9 | Hunt **rules** (adjacency, belly length, scoring, Training unrecorded) do not change with this option. | 2026-09-14 |
| E10 | Endosoma **keeps the playable belly** (void, `#` ring, raptor walks carrying the hunter). **Do not darken** `@` / `#` on Endosoma. Digest stance still darkens. | 2026-09-14 |
| E11 | Endosoma has its **own swallow-angle pools** in JSON (front / side / behind), separate from Digest’s current lines. Angle still comes from geometry. | 2026-09-14 |
| E12 | Path pick is a **session shuffle bag**: randomly order the pool, show each path once, then reshuffle. Bags live in **this process only** (not saved). Quit and relaunch may show the same scene twice in a row. Separate bag per pool. | 2026-09-14 |
| E13 | Stance is **live**: Options at the moment loss copy or Stats is drawn. Esc → change Post-swallow → Continue Hunt uses the new stance for later loss / Stats. Not written into the hunt autosave. | 2026-09-14 |
| E14 | **Hide** Oral Vore / Cock Vore / Anal Vore **for everyone** (Options rows and first-run vore-prefs screen). **Keep the code** (`VoreContentPreferences`, helpers, settings key). Hunt MVP is **OV**; other types may return later. Default enabled set stays OV/CV/AV in storage so a future UI can read it. | 2026-09-14 |
| E15 | Shipping `hunt_loss.json` narratives are **flat verification copy** (digest vs endosoma distinguishable). Richer prose can replace them in data later. | 2026-09-14 |
| E16 | Player-facing **general** spaces (README, tutorial, help, product blurbs) use **swallow** / **swallow you whole**. Digest wording stays on the Digest stance’s loss copy and Stats label only. | 2026-09-14 |

---

## Open questions

None. Q7–Q8 answered 2026-09-14.

Q1–Q8 answered 2026-09-14 (belly no-darken; separate swallow pools; session shuffle bag; live stance; hide OV/CV/AV, keep code; GAME OVER title unchanged; flat verification copy in `hunt_loss.json`; general player-facing spaces use **swallow** / **swallow you whole**, not digest).
