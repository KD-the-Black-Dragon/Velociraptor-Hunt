# Manual testing — PR1 hunt shell

How to run: `python -m src.main`

## Happy path

- [ ] Window title is **Velociraptor Hunt**
- [ ] Title screen shows the VELOCIRAPTOR banner and **HUNT** underneath
- [ ] Menu is **New Hunt**, **Stats**, **Options**, **Quit** (no career hub, no Load Game)
- [ ] New Hunt → name entry → Enter → weapon select (rifle / shotgun / revolver)
- [ ] Choosing a weapon drops you into a stub paddock (`@` inside `#` walls)
- [ ] Status line shows hunter name and weapon
- [ ] Esc from the paddock returns to the main menu
- [ ] Stats opens a stub screen; Esc returns to the menu
- [ ] Options still opens; Esc returns to the menu
- [ ] Quit leaves the game

## Edge cases

- [ ] Blank name becomes Anonymous on the paddock status line
- [ ] Esc on name entry returns to the menu
- [ ] Esc on weapon select returns to name entry
- [ ] First-run tutorial / vore prefs still appear if you have no settings yet
- [ ] User data folder is **Velociraptor Hunt** under `%LOCALAPPDATA%` (or the env override)

## Pointer

Full slice list: `openspec/changes/velociraptor-hunt/tasks.md` (PR1).
