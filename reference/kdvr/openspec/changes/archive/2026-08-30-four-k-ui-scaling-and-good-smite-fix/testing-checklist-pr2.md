# Manual testing — PR2 (temporary depth-1 sheep cleric)

**Temporary playtest aid.** Spawn window is `min_depth: 1` … `max_depth: 14`. **PR4 restores 12–14** before archive — do not ship this widen permanently.

Run: `python -m src.main`

## Setup

- [ ] **New Game** (or descend to a newly generated floor). Existing floors / loaded saves keep their already-spawned NPCs; eligibility applies at floor generation.

## Happy path

- [ ] On **depth 1**, a **sheep cleric** (glyph `p`, cyan) can appear among good allies (quota / RNG — may take a reroll or two)
- [ ] Cleric follows without **Smite**ing you when no evil is visible (verifies PR1 in the wild)
- [ ] When an evil is in Smite range, cleric may smite the evil, not you

## Notes / restore gate

- [ ] Remember: this early spawn is **temporary**; confirm PR4 before any public alpha rebuild
- [ ] Depths 12–14 still eligible until restore
