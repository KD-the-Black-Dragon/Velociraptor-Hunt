# Manual testing — PR1 (Dismiss ally targeting)

**How to run:** `python -m src.main`

PR1 only: Shift+D targeting + despawn. Help/tutorial lines come in PR2.

## Happy path

- [ ] New Game → find or summon a **good** ally (knight / squire / etc.)
- [ ] Press **Shift+D** → cyan `X` cursor appears (Examine-style)
- [ ] Move cursor onto the ally → **Enter**
- [ ] Ally disappears; log: *{name} exits the dungeon.*
- [ ] Confirm **no** turn advanced (monsters do not act from the dismiss alone)
- [ ] Plain **`d`** still opens **Drop** inventory (not dismiss)

## Edge cases

- [ ] Shift+D → cursor on empty floor / evil / self → Enter → *Invalid target. (Allied NPCs only)*; stay in targeting
- [ ] Esc cancels dismiss mode with no extra message
- [ ] Inventory / examine open → Shift+D does not start dismiss until those close
- [ ] Dismiss does **not** count as defeating the ally (past-run / defeat feel unchanged)

## Automated

```bash
python -m pytest tests/test_dismiss_ally_pr1.py -v
```
