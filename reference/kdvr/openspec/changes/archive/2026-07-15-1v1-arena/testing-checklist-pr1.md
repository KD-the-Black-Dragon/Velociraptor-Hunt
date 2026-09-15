# Manual testing — PR1: Interactive 1v1 arena

Run: `python -m src.main`

## Happy path

- [ ] Main menu **Ctrl+B** opens entity-id entry (not name entry, no save overwrite prompt)
- [ ] Three-column evil id list is visible; typing in the bottom buffer works
- [ ] Enter valid evil id (e.g. `rat`) starts a 1×10 hallway fight
- [ ] Status corner shows **Depth** = that enemy's `spawn.min_depth`
- [ ] Player loadout matches depth-jump gear for that depth (spot-check weapon/armor)
- [ ] Defeat enemy → modal **"You have defeated the …!"** → Enter → main menu
- [ ] No new Past Runs row after victory

## Validation

- [ ] Unknown id → `Unknown entity id.`
- [ ] Good/neutral id (e.g. `rabbit`) → `That entity is not Evil alignment.`
- [ ] **Escape** on entity entry → main menu

## Aquatic

- [ ] Arena vs `shark` (or other aquatic evil): water tile at far right; fight proceeds

## Save isolation

- [ ] With an existing autosave, start arena — autosave file unchanged after several turns
- [ ] **Ctrl+S** in arena shows `Game saved.` but does not update autosave timestamp/content
- [ ] After arena victory, prior autosave still loads normally

## Defeat / stunned

- [ ] Allow enemy to stun you (0 HP) — fight continues (heal if needed)
- [ ] Digested → normal game-over recap → Enter → main menu; no Past Runs row

## Regression

- [ ] **Ctrl+G** depth-jump still works
- [ ] Normal New Game / Load Game unchanged