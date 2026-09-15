# PR 1 — Manual checklist: Data loaders

Run `python -m src.main` from the project root. PR 1 does **not** wire JSON into spawn yet; gameplay is unchanged.

## Automated gate

```bash
python -m pytest tests/test_npc_data_pr1.py -v
python -m pytest tests/ -q
```

## Data files

- [ ] `data/entities.json` exists with wolf, knight, rabbit, shark
- [ ] `data/weapons.json`, `armor.json`, `potions.json`, `wands.json` exist (stubs)
- [ ] `data/SCHEMA.md` documents entity and item fields

## Loader smoke (optional Python one-liner)

```bash
python -c "from src.data.loaders import load_game_data; d=load_game_data(); print(len(d.entities.entities), d.warnings)"
```

Expect `4 ()` — four entities, no warnings on stock data.

## Regression

- [ ] Main menu → new game → dungeon plays as before (still hardcoded spawn)
- [ ] No crash on startup

## Data shape (optional)

- [ ] Wolf `vore_narratives.OV` is an array with 2+ variants in `entities.json`
- [ ] Wolf has `digestion_complete` and `digestion_player_modal` per OV/CV/AV
- [ ] All entities have `experience_points` (stored, not used in gameplay yet)

## Try ignore-unknown (optional)

Add `"mystery_stat": 99` to wolf in `entities.json`, run the one-liner above, confirm a warning appears; remove the field afterward. `experience_points` should **not** warn.