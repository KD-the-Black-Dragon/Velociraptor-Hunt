# Manual checklist — PR0: data-driven digest time (mechanics)

Run: `python -m src.main`

PR0 does **not** add `digest_time` to `entities.json` yet. All evil predators use default **6** strike ticks at 0 HP until PR1.

## Strike phase (default 6)

- [ ] Engulf a good ally (or use debug setup), reduce them to 0 HP inside a wolf/shark while held.
- [ ] Count digestion strike ticks before the NPC is removed — expect **6** ticks at 0 HP (slower than before).
- [ ] Player engulf at 0 HP: wait (`.)` six times — digestion modal opens on the **6th** strike tick.

## HP phase (unchanged)

- [ ] Engulfed prey still take `digestion_damage_per_tick` HP damage before strikes begin.
- [ ] No strike on the same tick HP drops to 0.

## Regression

- [ ] Rescue/release still clears strikes and allows regen afterward.
- [ ] Predator attack-only while holding; completion messages still appear when visible.
- [ ] *"You are being digested!!"* still logs only on 0-HP strike ticks (player).