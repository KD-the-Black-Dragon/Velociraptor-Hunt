# Manual checklist — PR5 SummonN

Run: `python -m src.main`

## Summon2 wolf (stock `entities.json`)

- [ ] First LOS: wolf summons **two rabbits** on distinct adjacent tiles when space allows
- [ ] Cramped tile (one free adjacent): only **one** rabbit spawns; still one-shot consumed
- [ ] Re-approach later: **no third rabbit**, no repeat log

## Regression (PR4)

- [ ] Summon log still FOV-gated (*"The wolf summons aid!"*)
- [ ] Chase/melee/vore unchanged after summon