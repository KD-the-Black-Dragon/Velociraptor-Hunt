# Manual testing checklist — PR1 (Re-identity)

## How to run

```bash
pip install -e ".[dev]"
python -m src.main
```

## Happy path

- [ ] Window title / branding shows **Gladiavore** (not KD's Vore Roguelike)
- [ ] Main menu shows large **GLADIAVORE** ASCII banner
- [ ] Credits title is **Gladiavore**
- [ ] First-run tutorial/onboarding welcome text says **Gladiavore** (if you reset settings)
- [ ] User data writes under `%LOCALAPPDATA%\Gladiavore\` (Windows) — new folder, not the old KDVR path
- [ ] Game still launches and New Game still works (dungeon loop still present; expected for PR1)

## Edge / regression

- [ ] Settings from old KDVR path are **not** auto-loaded (fresh Gladiavore dir)
- [ ] Options / credits / quit still work from main menu
- [ ] No crash on boot

## Not in this PR (do not fail PR1)

- Career hub, AUT combat, match cards, grapple rewrite
