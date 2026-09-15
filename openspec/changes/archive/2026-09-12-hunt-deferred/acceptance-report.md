# Acceptance — Hunt deferred (PR1–PR15)

**Status:** Provisionally accepted 2026-09-12. Designer wants to move on to other modules; raptor balance will be revisited.

**Live spec:** `openspec/specs/hunt/spec.md`  
**Canon:** this folder’s `DESIGN_CANON.md` plus foundation `archive/2026-09-04-velociraptor-hunt/DESIGN_CANON.md`

## Landed

PR1 Ctrl sidestep · PR2 right panel · PR3 adjacency swallow · PR4 last-known + `?` · PR5 mud prints · PR6 fatigue · PR7 off-center aim · PR8 dart · PR9 loss spectacle · PR10 Training Mode · PR11 rain beds · PR12 raptor mind · PR13 rifle scope / sounds / glyphs · PR14 memory / rain plan / locomotion · PR15 hunt difficulty JSON.

Cover-first evasion and tree-around navigation landed as playtest follow-through on the intelligence pack.

## Deferred (not in this change)

See `DESIGN_CANON.md` **Deferred** and `tasks.md` **Deferred**:

- Sound bait (D33) not wired
- Peek-once / same-gap-twice (D31 remainder)
- Broader balance playtest

## Tests

Targeted hunt suites for PR1–PR15 passed during implementation. Full `pytest tests/` was not required for this provisional close.
