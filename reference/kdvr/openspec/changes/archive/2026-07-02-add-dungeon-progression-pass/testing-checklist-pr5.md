# Manual checklist — PR5 (acceptance)

Run: `python -m src.main`

- [ ] Depth 1–3: density feels fair; not empty, not overcrowded
- [ ] Deeper floors feel somewhat denser (more threats)
- [ ] Three colored `0` runes per floor; step-on buff + brief local flash
- [ ] Rune buffs persist after descent; HP visible in HUD for vitality
- [ ] Good followers still follow; total fresh spawns reduced (not duplicated)
- [ ] Full regression: combat, vore, inventory, descent, followers
- [ ] `python -m pytest tests/ -q` all green