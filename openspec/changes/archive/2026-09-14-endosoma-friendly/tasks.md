# Tasks: endosoma-friendly

**Do not implement any PR until the designer authorizes that PR by name.**

Answering remaining questions or approving this folder is **not**
implementation authorization.

---

## Setup (design)

- [x] Create change folder (`proposal.md`, `design.md`, `tasks.md`, `DESIGN_CANON.md`)
- [x] Designer answers Q1–Q6 / E10–E14 (2026-09-14)
- [x] Designer approves flat verification copy (Q7) and swallow-only general wording (Q8)
- [x] Designer authorizes **PR1**

---

## PR1 — Post-swallow option and dual loss copy

One playable slice.

- [x] Settings: `post_swallow` `digest` \| `endosoma`, default digest, persist immediately, live read
- [x] Options row **Post-swallow** after Difficulty, cycle Left/Right/Enter
- [x] Hide OV/CV/AV rows from Options navigation and render; keep helper code
- [x] Skip first-run vore-prefs onboarding (mark complete / bypass); keep the module
- [x] `data/hunt_loss.json`: `digest_paths` (migrate current `digest`); `endosoma_paths`; `endosoma_swallow_{front,side,behind}` path pools
- [x] Session shuffle bags (in-memory, per pool, reshuffle when empty; not saved)
- [x] Digest stance: current swallow lines, belly darkens, digest path, GAME OVER digested, Stats **Times digested**
- [x] Endosoma stance: endosoma swallow path for the real angle, belly **no darken**, endosoma path, GAME OVER *The raptor got you.*, Stats **Times swallowed**
- [x] Training Mode follows the same live Options stance (still unrecorded)
- [x] Targeted tests (persist, hidden rows, skipped onboarding, both stances, no-fade, bag cycle, JSON migration)
- [x] Extend `openspec/specs/hunt/spec.md`
- [x] `testing-checklist-pr1.md` + checklist posted in chat
- [x] Designer playtest sign-off (2026-09-14)
- [x] Archive change (`openspec/changes/archive/2026-09-14-endosoma-friendly/`)

---

## Out of scope (unless designer adds them)

- Belly escape / non-loss ending
- Deleting vore-prefs code
- README/help rewrite until Q8
- Persisting shuffle bags
