# PR 4 Manual Testing Checklist — Player Swap

Run `python -m src.main` from the project root.

**Note:** Good and neutral NPCs are not spawned in normal play yet. Use the dev shell below or rely on automated tests for swap behavior.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_2.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Dev shell: spawn a knight beside you

```bash
python -c "from src.engine import GameEngine; from src.components import Alignment, Position; from src.systems.ai import spawn_test_npc; e=GameEngine(); p=e.player; pos=p.components[Position]; spawn_test_npc(e.world, x=pos.x+1, y=pos.y, species='knight', alignment=Alignment.GOOD); print('Knight spawned east at', pos.x+1, pos.y, '- restart main with same seed if needed')"
```

For in-game testing, spawn the knight before starting `python -m src.main`, or use a one-off script that runs the game loop.

---

## Swap with good/neutral (when NPC present)

- [ ] Bumping a **good** NPC swaps positions — no damage, no attack log
- [ ] Bumping a **neutral** NPC swaps the same way
- [ ] The swapped NPC does not act again that turn (you do not immediately get hit/chased by them)

## Evil wolves unchanged

- [ ] Bumping a wolf still deals damage and logs *"You hit the wolf …"*

## Stunned player

- [ ] While stunned, moving into a good/neutral tile shows *"You're too tired to move."*
- [ ] No swap occurs; your position is unchanged

## Regression

- [ ] Vore, **F2**, wait/regen, stunned movement unchanged
- [ ] **Escape** still quits (Ctrl+Q arrives in PR 6)

**Pass criteria:** Player can swap with good/neutral only; evil still attacks; swapped NPC skips once; pytest green.