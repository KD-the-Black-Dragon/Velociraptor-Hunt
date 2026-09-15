# Main Menu — Manual Testing Checklist

Run `python -m src.main` from the project root.

## Automated gate

```bash
python -m pytest tests/ -q
```

All tests should pass (271+ as of acceptance).

---

## PR 1 — Menu shell

- [ ] Application opens to a **black screen** with title **KD's Vore Roguelike** centered
- [ ] Five options near the bottom: New Game, Load Game, High Scores, Options, Exit
- [ ] **Up / Down** move the `>` highlight (wraps)
- [ ] **Enter** on **Exit** closes the application
- [ ] Window **X** closes the application (same as Exit)
- [ ] **Ctrl+Q** on the main menu does **nothing**

## PR 2 — Name entry

- [ ] **New Game** opens name entry (not straight into dungeon)
- [ ] Printable characters, **Backspace**, max **24** characters
- [ ] **Enter** with a name → HUD shows that name (not `KD's Vore Roguelike`)
- [ ] **Enter** blank → **Anonymous** in HUD
- [ ] **Escape** cancels → main menu
- [ ] Recap shows display name and **Digested by …** fate; **no** score line

## PR 3 — Options and persistence

- [ ] **Options** lists **Oral Vore**, **Cock Vore**, **Anal Vore** with ON/OFF
- [ ] **Up / Down** highlight; **Left / Right** or **Enter** toggles
- [ ] Cannot disable the last enabled type
- [ ] **Oral Vore** can be OFF when Cock or Anal remains on
- [ ] **Escape** returns to menu; settings persist across restart (`{user_data}/settings.json`)
- [ ] New game respects saved prefs for vore initiation

## PR 4 — Flow integration

- [ ] **Ctrl+Q** during gameplay → `Do you want to quit? (Y/n)`
- [ ] Capital **Y** → main menu; lowercase **n** → resume
- [ ] Other keys → `Please type capital 'Y' or lowercase 'n' only.`
- [ ] **Ctrl+Q** during vore, digestion, or recap modal → **no-op**
- [ ] Recap **Enter** → main menu (not exit)
- [ ] **Load Game** / **High Scores** show **Coming soon**; **Escape** or **Enter** backs out

## Regression

- [ ] Movement, FOV, combat, vore, digestion, NPC factions unchanged
- [ ] Debug keys **R**, **F2**, **S** work during gameplay
- [ ] Engulfed struggle, mercy, NPC rescue, digestion strikes normal
- [ ] CP437-safe log text; FOV-gated off-screen messages