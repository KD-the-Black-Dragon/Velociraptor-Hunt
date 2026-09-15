# Acceptance Report: add-good-npc-roster

**Date:** 2026-07-30  
**Scope:** Expand good-aligned stock allies — dog squire, retuned dog knight (spawn + combat), ferret guard, lion warrior, otter warden, boar-at-arms, ram crossbow, sheep cleric, badger champion; names and introductions; equal-length depth bands.

## Automated verification

### Change-scoped

Registry load smoke (manual agent check during PR1): all nine good ids load; name pools and introductions present; ram/sheep melee stats equal ranged stats; knight spawn 5–7 and combat table applied.

### Full suite

**Skipped** — designer waiver for this data-only change (see `tasks.md`).

## Manual verification

Designer playtest signed off (2026-07-30): looks good; proceed to PR2 archive.

## Live specs

- `openspec/specs/npc-data/spec.md` — multi-species good ally roster note

## Stock content

| File | Change |
|------|--------|
| `data/entities.json` | 8 new goods; knight spawn 5–7 + combat buff |
| `data/names.json` | Title-scheme pools for new goods; knight Sir pool unchanged |
| `tools/_apply_good_npc_roster_pr1.py` | One-shot apply helper used for PR1 |

## Outcome

**Accepted.** Archived to `openspec/changes/archive/2026-07-30-add-good-npc-roster/`.
