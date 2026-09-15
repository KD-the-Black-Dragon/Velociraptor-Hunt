# Manual testing — PR1 (spawn OR semantics)

## How to run

`python -m src.main`

## Happy path

- [ ] New Game with all three vore types on — floors populate normally (stock `requires_vore_types: []`)
- [ ] New Game with only one type on — floors still populate; no crash / empty-world surprise from the OR change alone
- [ ] Arena / normal play still starts (no regression from spawn helper)

## Notes

PR1 does **not** yet restrict which types monsters attempt (that is PR2). Stock has no non-empty capability lists, so PR1 is mostly invisible in play without a modded entity.

Optional mod check: entity with `"requires_vore_types": ["CV","AV"]` should **appear** when only CV is enabled (would have been blocked under the old AND gate).
