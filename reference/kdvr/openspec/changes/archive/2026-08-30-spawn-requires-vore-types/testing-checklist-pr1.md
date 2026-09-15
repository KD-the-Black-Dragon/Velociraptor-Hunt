# Manual testing — PR1 (spawn.requires_vore_types gate)

How to run: `python -m src.main`

PR1 is mostly invisible with stock data (no `requires_vore_types` gates yet). Confirm **no regression** on normal play; content/Sample Mod land in PR2.

## Happy path

- [ ] New Game with all three vore types On — floors still populate with a normal mix of enemies
- [ ] New Game with only **OV** enabled (CV/AV Off) — floors still get a full-feeling density of enemies (not sparse empty maps)
- [ ] Same with only **CV** or only **AV** — density still looks normal
- [ ] Descend a few floors — spawn still happens; no crash

## Summons / allies

- [ ] Potion of alliance still summons a good ally when goods exist for the depth
- [ ] NPCs that summon (if encountered) still function; no traceback

## Arena (if you use it)

- [ ] Start an arena fight vs a stock evil — enemy appears as usual

## Save / load

- [ ] Autosave / load mid-run — existing NPCs remain; no despawn from this gate

## Performance

- [ ] No noticeable hitch on floor entry vs before

## Full checklist

See also `openspec/changes/spawn-requires-vore-types/tasks.md` (PR1).
