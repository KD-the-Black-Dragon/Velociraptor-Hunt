# Manual testing — PR5 fire + tranq win

How to run: `python -m src.main`

## Happy path

- [ ] **F** opens targeting (cyan **X**). If the raptor is in sight, the cursor starts on it
- [ ] Factors appear only after F (range, aiming/no aiming, blind fire, ammo)
- [ ] Esc in targeting returns to walking, does **not** quit the hunt
- [ ] F or Enter in targeting fires, spends ammo, and a dart travels in a straight line
- [ ] Blind-fire: aim the X at a tile you cannot see; if the line hits the raptor it still counts
- [ ] Shotgun at hugging range can drop the raptor even unaimed
- [ ] Rifle unaimed, even close, only grazes
- [ ] When HP hits 0: map freezes, **You fire your {weapon}!**, bright **The raptor is tranquilized!!**
- [ ] Any key → **You win!** and a short score list
- [ ] Any key again → main menu

## Edges

- [ ] Trees stop the shot (no HP loss)
- [ ] Empty shot still spends a round
- [ ] Running is listed as a factor and makes the shot worse
- [ ] A / A deep aim listed as aiming / deep aim

## Pointer

`openspec/changes/velociraptor-hunt/tasks.md` (PR5).
