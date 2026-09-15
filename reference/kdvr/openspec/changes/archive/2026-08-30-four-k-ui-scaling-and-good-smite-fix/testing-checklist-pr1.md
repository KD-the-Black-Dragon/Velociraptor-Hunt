# Manual testing — PR1 (good Smite vs player)

Run: `python -m src.main`

## Happy path

- [ ] Meet or spawn a good Smite ally (sheep cleric at depths 12–14, or wait for PR2 depth-1 aid)
- [ ] With **no evil** visible and the ally following nearby (about 2–5 tiles): ally must **not** smite you; no “smites you” in the log; HP does not drop from Smite
- [ ] With an **evil** in Smite range while you are also nearby: ally may smite the evil; must **not** smite you

## Regression

- [ ] Evil Smite casters (e.g. owl mage / slime with Smite) still can smite the player at range
- [ ] Good melee allies still follow without bumping/attacking you
- [ ] Save/load not required for this PR (combat-only behavior)

## Notes

Full playtest of sheep cleric on depth 1 is deferred to **PR2**. Until then, depth-jump toward 12–14 or find a natural cleric spawn.
