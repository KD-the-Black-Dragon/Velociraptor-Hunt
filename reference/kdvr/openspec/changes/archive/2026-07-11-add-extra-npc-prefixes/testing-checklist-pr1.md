# Manual testing — PR1 (prefix infrastructure)

Run: `python -m src.main`

Infrastructure PR — behavior visible once PR2 content lands. PR1 validation is primarily automated tests; optional dev-console spawn if test helpers exist.

## Automated (agent runs)

- [ ] Prefix filter tests pass (`pytest` targeted suite for PR1)

## Optional smoke (if spawning prefixed NPCs via tests/debug)

- [ ] Floor spawn still applies Elite on evil species when registry includes elite row
- [ ] No crash when prefix chance succeeds but no candidates match (future-gated species)

## Regression

- [ ] Summoned allies (potion of alliance) do **not** receive random prefixes
- [ ] Save/load preserves `NpcPrefix` id on prefixed NPC