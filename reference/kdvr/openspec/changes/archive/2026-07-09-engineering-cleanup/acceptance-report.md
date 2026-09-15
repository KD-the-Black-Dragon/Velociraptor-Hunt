# Acceptance Report: engineering-cleanup

**Date:** 2026-07-09  
**Scope:** Save soft-drop + spawn weight 0 (PR1); flaky test hardening (PR2); tcod `console.rgba` freebie (PR3).

## Delivered

| Area | Outcome |
|------|---------|
| **AGENTS.md** | Mods shipped; save forward-compat / soft-drop discipline |
| **Save sanitize** | Unknown inventory/floor items and unknown SpeciesId NPCs stripped on load; caution log notice |
| **Spawn weight 0** | `spawn.weight` / `spawn_weight` allow 0 = never spawn (definition kept) |
| **Live spec** | `openspec/specs/save-load/spec.md` soft-drop requirements |
| **Flakes** | Perf p95 skipped; Summon1 / vore modal / RangeN setups isolated & deterministic; frustration DEBUG snarl tests de-flaked |
| **Freebie** | Tests use `console.rgba` instead of deprecated `console.tiles` |

## Out of scope (deferred)

- Version-range migration hook (optional; not needed for additive fields)
- Door spite gameplay (stays in `todo`)
- New features

## Automated verification

### Full suite (acceptance)

```bash
python -m pytest tests/ -n 6 --tb=line -q
```

| Result | Count |
|--------|-------|
| Passed | 1253 |
| Skipped | 2 (perf p95 budget, by design) |
| Failed | 0 |
| Duration | ~13m 51s |

### rgba freebie (sample, FutureWarning as error)

```bash
python -W error::FutureWarning -m pytest tests/test_ui_modals.py tests/test_ui_message_log.py ...
```

| Result | Detail |
|--------|--------|
| **PASS** | 233 UI/render tests; no `rgba` FutureWarnings |

## Manual verification

Designer signed off that the change is good (2026-07-09). Soft-drop path covered by automated tests; normal play/load path unchanged.

## Live specs

- `openspec/specs/save-load/spec.md`
