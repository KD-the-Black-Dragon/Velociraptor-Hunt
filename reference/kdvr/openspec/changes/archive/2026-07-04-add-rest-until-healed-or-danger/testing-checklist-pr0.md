# Manual checklist — PR0: Rest until healed or danger

Run: `python -m src.main`

## Pre-checks (no time passes; **red** messages)

- [ ] At **full HP**, press **`5`** → *"You are already at full health."* (red)
- [ ] With **evil in your FOV**, press **`5`** → *"It's too dangerous to rest now!"* (red)
- [ ] While **engulfed**, press **`5`** → *"This is no time to rest!"* (red)

## Rest loop

- [ ] Injured, safe: **`5`** → *"You start resting."* then silent turns; ends *"You are fully healed."*
- [ ] Resting: evil enters your FOV → *"Danger approaches!"* (red)
- [ ] Resting: enemy attacks (hit or miss) → *"It's hard to rest while under attack!"* (red)
- [ ] Resting: ally in your sight sees evil you do not → *"{Name} shouts in alarm!"* (red); rest stops
- [ ] Safe, not reaching full HP within 100 turns → *"You finish resting."*
- [ ] **Stunned** at low HP: **`5`** works; no per-turn tired message during rest

## Regression

- [ ] Numpad **5** waits **one** turn only
- [ ] **`.`** and **Shift+H** still single wait
- [ ] Good NPCs **never** shout in alarm when you are not resting