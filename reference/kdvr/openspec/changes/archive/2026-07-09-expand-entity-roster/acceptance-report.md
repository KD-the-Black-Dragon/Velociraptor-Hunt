# Acceptance Report: expand-entity-roster

**Date:** 2026-07-09  
**Scope:** Stock entity roster expansion — ROUS cave rat, silent slime, tarantula stub, fox archer, gnoll mercenary, roc, owl mage micro-vore narrative, deep stubs (wyvern/drake/gryphon/dragon); deprecate giant_spider weight 0.

## Automated verification

### Change-scoped

```bash
python -m pytest tests/test_expand_entity_roster_pr1.py tests/test_entity_placeholder_pr4b.py -v
```

| Result | Detail |
|--------|--------|
| **PASS** | Roster load, bands, fox/gnoll ranged split, spider weight 0 |

### Full suite

```bash
python -m pytest tests/ -n 6 --tb=line -q
```

| Result | Count |
|--------|-------|
| Passed | 1324 |
| Failed | 0 |
| Skipped | 2 |
| Duration | ~9m 24s |

## Manual verification

Designer smoke test signed off (2026-07-09): no obvious errors; balance notes deferred to later play.

## Live specs

- `openspec/specs/npc-data/spec.md` — placeholder + weight-0 deprecation note

## Stock content

| File | Change |
|------|--------|
| `data/entities.json` | Retheme cave_rat; deprecate giant_spider; add 10 species |
| `tools/_apply_expand_entity_roster.py` | Regenerator for themed blocks |
