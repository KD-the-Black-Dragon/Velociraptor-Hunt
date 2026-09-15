# Design: Engineering maintainability pass

| Field | Value |
|-------|-------|
| **Date** | 2026-07-09 |
| **Status** | **Design locked** (designer answers 2026-07-09) |
| **Change id** | `engineering-maintainability` |
| **Spec targets** | Thin `openspec/specs/engineering/spec.md` (new); extend `save-load` for field inventory; no gameplay specs |

---

## Goals

1. Lower maintenance cost of the two mega-files without changing what the player experiences.
2. Make future content PRs cheaper to test and safer near saves.
3. Leave agent-facing rules so strings and save defaults do not re-scatter.
4. Prefer **smaller PRs + frequent designer smoke** over large bangs (designer preference).

## Non-goals

- Performance optimization (unless a pure move accidentally improves locality — do not chase).
- Rewriting AI **decision priority** / explore BFS **semantics** / distant throttle **rules** (cleanup may rename and reorganize code that implements them).
- Splitting `entities.json` narratives.
- i18n / full localization framework (catalog discipline only).

---

## Locked product constraints

| Constraint | Detail |
|------------|--------|
| **Gameplay freeze** | No intentional changes to combat outcomes, AI *choices*, spawn rates, digests, UI layout, or difficulty math. Refactors may reorganize code; behavior must match. |
| **Save freeze** | Stay on `save_format_version = 1`. Soft-drop policy from prior cleanup stays. |
| **Import path** | Production: `from src.engine import GameEngine` and `from src.systems.ai import run_monster_turns` (and other true public names) must keep working. Tests may be updated to clearer imports during **deeper cleanup** PRs. |
| **Terminology** | defeated / stunned / digested in any new strings. |
| **Manual testing** | **Mandatory basic smoke after every PR** (see below). Never mark a PR complete on automated green alone. |

---

## Designer decisions (locked)

| Q | Answer |
|---|--------|
| **Q1 Manual cadence** | Smoke anything that could have been affected. Always: **launch game, new game, reach a game over** (or an equally clear end-of-run path), plus PR-specific paths. Past false “all clear” crashes make this non-optional. |
| **Q2 PR order** | Helpers → messages → save → engine slices → AI slices → accept. |
| **Q3 Depth** | **Deeper cleanup** (clearer names, stricter public API, delete proven-dead code) — but **split into many small PRs**. More risk ⇒ slower pace, more smoke gates. |
| **Q4 Messages** | **Full remaining** player-visible message-log literals into `messages.py`. Session/debug free-form OK; entity JSON narratives stay in data. |

---

## Mandatory smoke template (every PR)

Agent posts a **checkbox checklist in chat** after each PR. Base block (always):

```text
How to run: python -m src.main

[ ] Game launches (main menu appears; no traceback on start)
[ ] New Game starts a run (map, log, player visible)
[ ] Play until game over is reachable (e.g. allow digestion defeat, or document alternate end used)
[ ] No crash during the above
```

Plus **PR-specific** bullets (inventory, rest, descend, save/load, combat, come-here, etc.) when that PR touches those paths.

**Rule:** Do not start the next PR until designer sign-off (or explicit “skip smoke for this PR” from designer).

---

## PR plan (risk ladder, many small slices)

| PR | Focus | Risk | Deeper cleanup? |
|----|-------|------|-----------------|
| **PR1** | Test helpers (spawn-at-depth / difficulty) | Low | N/A (new helpers only) |
| **PR2** | Message catalog + full remaining log literals | Low–med | Policy only |
| **PR3** | Save field inventory, defaults, migrate stub, tests | Low–med | Docs/tests; no soft-drop product change |
| **PR4** | Engine: extract **floor** lifecycle only | Med | Mechanical move |
| **PR5** | Engine: extract **turn** pipeline only | Med | Mechanical move |
| **PR6** | Engine: extract **input** (+ rest glue if still large) | Med | Mechanical move |
| **PR7** | Engine: **deeper cleanup** (names, public surface, dead code) | Med–high | Yes — own PR |
| **PR8** | AI: package scaffold + extract **explore** | High | Mechanical move + re-exports |
| **PR9** | AI: extract **chase** + **targeting** | High | Mechanical move |
| **PR10** | AI: extract **movement** + **visit** + orchestration (`run_monster_turns`) | High | Mechanical move |
| **PR11** | AI: **deeper cleanup** (public API, renames, dead code, test import updates) | High | Yes — own PR |
| **PR12** | Full suite + archive | Low | N/A |

If a slice is still too large mid-implementation, **split further** (e.g. PR9a chase only, PR9b targeting) rather than batching.

**Out of scope forever in this change:** narrative externalization, perf budget module, gameplay features, balance packs.

---

## PR1 — Test helpers for spawn-at-depth / difficulty

### Problem

Tests that need “species at depth under difficulty” copy-paste or pin live `data/`.

### Design

Helpers (names illustrative):

| Helper | Role |
|--------|------|
| `spawn_species_at(engine, species_id, x, y, *, floor_depth, difficulty_id, …)` | Place one NPC via production-faithful spawn path (or thinnest faithful subset) |
| `engine_at_depth` / set difficulty on engine | Convenience for engine-level tests |
| Fixture-friendly overload | Pinned mini-registry so balance churn does not break tests |

### Rules

- Do not pin live stock balance numbers in asserts.
- Prefer isolated entity defs for scaling math; stock ids only for structural smoke.
- Docstring: when vs `spawn_test_npc` / digest fixtures.

### Smoke

Base template + “helpers do not affect runtime if unused” is still: launch + new game (production path untouched but catch import/package mistakes).

---

## PR2 — Message / string catalog discipline

### Design

1. **Policy** in `openspec/specs/engineering/spec.md`: player-visible message log / caution → `messages`; session/debug free-form OK; exceptions free-form OK; entity narratives stay in JSON.
2. **Full remaining** `message_log.add` literals / f-strings not via `messages.*` → named functions. **Wording unchanged.**
3. Do not multi-file `messages.py` unless clearly necessary after migration.

### Smoke

Base template + glance that common log lines still look normal (pickup, hit, stunned).

---

## PR3 — Save codec / snapshot schema hardening

### Deliverables

| Item | Detail |
|------|--------|
| Field inventory | Run keys + entity record + missing→default |
| Additive default tests | Stripped optional keys still load |
| Round-trip test | Compact in-memory encode/decode |
| `migrate_run` | Identity stub for v1; **no version bump** |
| Agent checklist | New optional state / soft-drop / true break rules |

### Smoke

Base template + **save mid-run and load** (if autosave path easy) or new game → save trigger → continue.

---

## PR4–PR6 — Engine extract (mechanical, one concern each)

### Current shape

| Region | Responsibility |
|--------|----------------|
| Floor | `new_game`, `initialize_floor`, descend, spawn, prefetch |
| Turn | `_consume_player_turn`, `_run_world_turn`, regen, digestion, haste |
| Input | `handle_event`, modals, gameplay keys, debug keys |
| Rest / render | Keep with turn or input if small; extract only if still bloated |

### Approach

Facade + modules (package `src/engine/` **or** sibling `engine_floor.py` etc. — implementer picks least import pain). Public: `from src.engine import GameEngine`.

### Per-PR rule

- **One concern only** (floor **or** turn **or** input).
- Move first; no renames of public methods; no dead-code deletion yet (that is PR7).
- Module-level functions taking `engine` OK if circular imports force it.

### Smoke (each of PR4–PR6)

Base template + paths that PR touched:

| PR | Extra smoke |
|----|-------------|
| PR4 floor | New game, **descend** one floor if possible, regenerate if still bound |
| PR5 turn | Move, wait/rest a few turns, get hit, ensure world phase runs (monsters act) |
| PR6 input | Inventory, examine, pickup, close door if easy, quit to menu without hang |

---

## PR7 — Engine deeper cleanup

Allowed in **this PR only** (not mixed with a large extract):

| Cleanup | Rules |
|---------|-------|
| **Rename** private helpers / internal modules for clarity | Update all call sites in same PR; public `GameEngine` method names used by tests stay unless tests updated in-PR |
| **Public surface** | Document intended public methods; thin wrappers stay for compatibility if needed |
| **Dead code** | Delete only with proof (no references in src/tests) |
| **Import hygiene** | Reduce circular imports; lazy imports only where already patterned |
| **Not allowed** | Changing turn order, spawn counts, modal semantics, save payload shape |

### Smoke

Full base + new game → play a few turns → inventory → rest → descend or stairs check → force or wait for **game over** path → confirm return to menu/end state without crash.

---

## PR8–PR10 — AI extract by intent (mechanical)

### Proposed modules

| Module | Contents |
|--------|----------|
| `explore` | Terrain/BFS caches, goals, frustration, oscillation |
| `chase` | Pursuit momentum, memory chase |
| `targeting` | `pick_evil_*`, `pick_good_chase`, visible hostiles |
| `movement` | Chase direction, try move, swap/bump glue |
| `visit` | `_run_monster_visit`, plan execution, predator holding |
| `throttle` | Distant/busy half-turn (small) |
| Package / shim | `run_monster_turns` + re-exports |

### PR slices

| PR | Move |
|----|------|
| PR8 | Package scaffold + **explore** only; re-export surface so existing imports still work |
| PR9 | **chase** + **targeting** |
| PR10 | **movement** + **visit** + `run_monster_turns` orchestration leftovers |

If any PR diff is huge, split further before merge/sign-off.

### Mechanical rules

- No intent priority reordering.
- No throttle constant or explore semantic changes.
- Re-exports keep `from src.systems.ai import …` working through PR10 (tests can still use old paths).

### Smoke (each)

Base template +:

- Bump-fight an evil
- Observe monsters move / chase when in view
- (PR9+) good ally or come-here if convenient
- Save/load once across the AI series if easy

---

## PR11 — AI deeper cleanup

| Cleanup | Rules |
|---------|-------|
| **Public API** | Define `__all__` / documented exports: `run_monster_turns`, pick_* used by production, etc. |
| **Test imports** | Prefer updating tests to import from submodules or public names; drop blanket private re-exports only after tests updated |
| **Renames** | Clearer private names **with full call-site update** |
| **Dead code** | Grep-proven unused only |
| **Not allowed** | Changing who attacks whom, explore goal selection outcomes, distant throttle eligibility |

### Smoke

Base + fight + explore a bit of a floor + ally/come-here if available + **game over** + save/load.

---

## PR12 — Acceptance

- Full suite `python -m pytest tests/ -n 6` (re-run failures only).
- Acceptance report; archive; complete todo rows; clear AGENTS pointer.
- Final smoke: launch → new game → short play → save/load → game over path.

---

## Testing strategy summary

| Layer | Policy |
|-------|--------|
| Automated | Targeted suite every PR; parallel `-n 6` when multi-file; full suite only PR12 (or after PR11 if designer wants early full run) |
| Manual | **Every PR** — base template + affected paths; wait for sign-off |
| Gameplay freeze | Assert via existing tests + designer eyes; no “balance” edits |

---

## Performance

Expected **neutral**. If a regression appears after AI/engine PRs, fix the regression in a tiny follow-up PR — do not expand into a perf project.

---

## Resolved decisions

| # | Decision | Choice |
|---|----------|--------|
| R1 | Bundle | One OpenSpec change; **12 PRs** (small slices) |
| R2 | Gameplay | Freeze behavior |
| R3 | Save version | Stay v1; identity migrate stub |
| R4 | AI imports | Stable through extract PRs; cleanup may tighten in PR11 |
| R5 | Messages | Full remaining log literals |
| R6 | entities.json | Do not split narratives |
| R7 | Order | Helpers → messages → save → engine×4 → AI×4 → accept |
| R8 | Cleanup depth | Deeper cleanup in **dedicated** PR7 (engine) and PR11 (AI) |
| R9 | Manual | Mandatory smoke every PR including helpers/messages/save |
| R10 | Blast radius | Prefer extra PR split over large combined diffs |

---

## Open questions

**None** — design locked. Coding starts only when designer **authorizes PR1**.
