# Manual checklist — PR1: digest_time content

Run: `python -m src.main`

## Per-species digest pacing

- [ ] Wolf engulfs knight (or ally), prey at 0 HP — **3** strike ticks before NPC removal.
- [ ] Shark engulfs prey at 0 HP (water floor if spawned) — **10** strike ticks before removal (noticeably slower than wolf).
- [ ] Player engulfed by wolf at 0 HP — digestion modal opens on **3rd** wait (`.`).

## Regression (PR0 + digestion core)

- [ ] HP damage phase unchanged (`digestion_damage_per_tick`).
- [ ] No strike on the tick HP drops to 0.
- [ ] Rescue/release clears strikes; regen blocked while `strikes >= 1`.
- [ ] Completion messages and player strike log unchanged.

## Data

- [ ] `data/entities.json`: wolf has `"digest_time": 3`, shark has `"digest_time": 10`.
- [ ] Tune values freely in JSON — no code change required for balance tweaks.