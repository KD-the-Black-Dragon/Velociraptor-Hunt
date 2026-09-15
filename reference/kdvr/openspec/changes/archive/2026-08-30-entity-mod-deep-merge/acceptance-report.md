# Acceptance Report: entity-mod-deep-merge

**Date:** 2026-08-30  
**Scope:** Selective deep merge for mod `entities.json` (existing ids inherit omitted fields); docs/spec update; `MODDING_README.txt` refresh on launch when missing or stale.

## Automated verification

### Change-scoped

| Suite | Result |
|-------|--------|
| `tests/test_mod_json_merge.py` | passed |
| `tests/test_mod_entities_pipeline.py` | passed |
| `tests/test_mod_seed_readme.py` | passed |

Combined targeted runs during PR1–PR2 (and README follow-up): **29 passed**.

### Full suite

**Deferred by designer** — full `pytest tests/` regression reserved for release-build anticipation; not run at archive for this change.

## Manual verification

Designer playtest / doc sign-off:

- PR1: entity deep-merge behavior (weight-0 wolves, patches, bad incomplete new id)
- PR2: docs + live modding spec; README refresh on launch

## Live specs / docs

- `openspec/specs/modding/spec.md` — entity deep merge vs other id catalogs; README refresh requirement
- `README.md` — Modding rules + patch example
- `data/SCHEMA.md` — merge table
- `src/mods/seed_sample.py` — shipped guide text + `refresh_modding_readme`

## Key implementation

| Area | Change |
|------|--------|
| `src/mods/json_merge.py` | `deep_merge_json` (objects recurse; arrays/scalars replace) |
| `src/mods/pipeline.py` | Entities `entry_merge="deep"`; other id catalogs remain full-replace |
| `src/mods/seed_sample.py` | Refresh `MODDING_README.txt` each launch when missing/differ; Sample Mod create-once |
| Tests | Pinned fixtures only — no live `data/entities.json` pins |

## Outcome

**Accepted** (full-suite deferred). Archive to `openspec/changes/archive/2026-08-30-entity-mod-deep-merge/`.
