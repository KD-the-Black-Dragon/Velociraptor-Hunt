# Proposal: First-run onboarding (tutorial + vore preferences)

## Problem

New players have no Roguelike background. The main menu and in-game help assume familiarity with movement, turns, and survival. Vore-as-game-over is central to the design but is not surfaced before play. Vore narrative preferences should be chosen deliberately on first launch, not discovered inside Options.

## Solution

Replace the cold start-to-main-menu path with a short **onboarding sequence** (first launch only):

1. **Tutorial prompt** — Yes / No (persisted; never shown again after answered).
2. **Quick Start tutorial** (if Yes) — two Enter-advanced pages, then a reminder page.
3. **Vore preferences screen** (first launch only) — Oral / Cock / Anal toggles plus confirm.
4. **Main menu**.

The same Quick Start tutorial remains available from **Options → Tutorial** (paginated; no vore prefs screen on repeat visits).

## Scope

- First-run tutorial prompt (exact copy, no default selection, enhanced highlight)
- Paginated Quick Start (no scrolling; Enter advances pages)
- Post-flow notices (decline message; post-tutorial reminder)
- First-run vore preference screen (OV / CV / AV + confirm)
- Persistence flags in AppData `settings.json`
- Options → Tutorial entry

## Out of scope

- In-game contextual tutorials
- Replacing or duplicating F1 help wholesale
- Comprehensive mechanic reference (inventory screen, allies, throw picker, etc.)

## PR plan

| PR | Scope |
|----|--------|
| PR1 | Onboarding flow, paginated tutorial content, vore prefs screen, persistence, Options → Tutorial, tests |

Single PR unless playtest reveals size pain.