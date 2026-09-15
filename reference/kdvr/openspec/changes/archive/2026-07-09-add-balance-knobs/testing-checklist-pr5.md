# Manual testing checklist — PR5 (content tune)

Run: `python -m src.main`

This PR **changes stock feel**. Tune further via JSON if something is too harsh/soft.

## Floor 1 protection

- [ ] On **Nightmare** (and others): floor 1 enemies still feel approachable (no depth bonus at depth 1)
- [ ] Early game not a brick wall on Easy/Normal

## Difficulties (Options → pick, New Game)

| Difficulty | Expect roughly |
|------------|----------------|
| **Easy** | Fewer NPCs; more runes (4); slow depth scale; no elites |
| **Normal** | Mild depth scale by mid floors; rare elites from ~depth 5 |
| **Hard** | Noticeably tougher deep floors; denser; rune pieces ×2; elites more often |
| **Nightmare** | Steep HP/AC/damage; denser; only 2 runes/floor; pieces ×2; frequent elites deep |

- [ ] Easy short run feels forgiving
- [ ] Normal: by depth 5–10 evils are clearly stronger than depth 1
- [ ] Hard: wardings need 2 pieces for +1 AC **and** pieces multiplier 2 → effectively slower AC growth
- [ ] Nightmare: deep floors threatening; see **Elite wolf** / **Elite bat** sometimes
- [ ] Past Runs shows difficulty **before** depth (`Hard - Depth N - …`)

## Placeholders

- [ ] See **cave rat** (`c`) early floors
- [ ] **giant spider** (`S`), **kobold** (`o`), **tunnel slug** (`u`) at deeper bands
- [ ] Examine shows `[placeholder]…`
- [ ] Stub vore text is utilitarian / marked placeholder (OK for now)

## Regression

- [ ] Good knights still follow; not depth-scaled
- [ ] Save/load mid-run
- [ ] Summons not Elite
- [ ] Floor gen stable

## Automated

- [x] Targeted balance/entity/rune suites green after content change

## Notes for further JSON tweaks

| File | Knobs |
|------|--------|
| `data/depth_scaling.json` | curves, density, runes override, pieces mult, prefix_spawn |
| `data/npc_prefixes.json` | elite flat bonuses |
| `data/floor_runes.json` | warding pieces (stock 2) |
| `data/entities.json` | filler weights/depths/stats |
