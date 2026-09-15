# Manual checklist — PR 4: Aquatic combat, shark, mobility escape

Run after `python main.py`. Sign off before PR 5.

## Aquatic combat

- [ ] On a floor with water (`~`), sharks (`s`) appear in deep water (two per water floor)
- [ ] Floors without water have **no** sharks
- [ ] Shark in water can **bump-attack** player/NPC on adjacent land without entering land
- [ ] Shark cannot walk onto land tiles

## Flyers (future-proofing)

- [ ] Ground player still blocked by water; FOV still passes through water

## Vore escape

- [ ] Ground player escaping engulf does **not** land on water (falls back to nearby land)
- [ ] Vore initiation still works when predator and prey are on opposite sides of a shore

## Population

- [ ] Wolf/knight/rabbit counts on land unchanged when sharks are present