# Acceptance — Velociraptor Hunt foundation (PR1–PR11)

**Status:** Accepted by designer playtest (PR11 sign-off 2026-09-01).

**Live spec:** `openspec/specs/hunt/spec.md`  
**Canon:** `DESIGN_CANON.md` (this folder)

## Landed

Playable one-hunt loop: New Hunt → name → weapon → paddock; Continue Hunt / abandon; Stats per difficulty.

PR1 identity shell · PR2 paddock/tank/AUT/FOV · PR3 gait/aim · PR4 raptor body · PR5 fire/tranq · PR6 rain/clues · PR7 clock/ring · PR8 swallow/belly/digest · PR9 raptor mind · PR10 stats/help · PR11 autosave/abandon/difficulty boards.

## Deferred (not in this change)

See `tasks.md` **Deferred**: aim off-center, run fatigue, last-known raptor, right-side panel, projectile animation, rain audio samples, practice dummy, game-over modal, sounds-as-map-symbols-only, footprint TTL, relative-score panel, KDVR-exact belly, vore modals, adjacency-without-attack win, Shift+numpad strafe with NumLock on, raptor-AI dissection.

## Tests

Targeted hunt suites passed through PR11.

Full `pytest tests/` (2026-09-04):

- **447 passed first try** (`-n 4`); same 447 green on the step-8 rerun.
- **2 recovered serially** (hunt menu isolation after Continue Hunt): `test_credits_menu_pr2::test_hunt_menu_omits_credits`, `test_past_runs_menu_pr4::test_build_menu_options_is_hunt_shell`.
- **14 failed twice** and **19 collection errors** are leftover Gladiavore/KDVR tests (career hub vs hunt shell, `PrefetchParams`, missing `src.systems.inventory` / `digestion` / `naming`). Not hunt product regressions; not fixed.
