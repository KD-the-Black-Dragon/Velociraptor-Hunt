# Enhancements 2 — Manual Testing Checklist

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_2.py tests/test_examine.py tests/test_acceptance.py -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Identity and combat (normal play)

- [ ] Wolves chase and attack on sight
- [ ] Combat logs use *"the wolf"* — no *"monster"*
- [ ] Defeat log uses *"The wolf was defeated."* (or proper name if set in a dev test)
- [ ] No `ProperName` on default wolf spawns

## Vore logs (evil wolves)

- [ ] Missed vore attempt — *"You evaded the wolf's vore attempt."*
- [ ] Escape engulf — *"You escape from the wolf."*
- [ ] If a wolf has `ProperName("Fang")` in a dev test, logs use *Fang* / *Fang's* without *"the Fang"* (modal text unchanged)

## Examine

- [ ] **x** — cyan cursor on player tile; no turn consumed
- [ ] Arrows move cursor only
- [ ] **Enter** on wolf — description modal (vicious/ferocious); text not in message log
- [ ] **Escape** — dismiss modal to cursor; **Escape** again exits examine
- [ ] Empty floor + **Enter** — *"There is nothing of interest here."*
- [ ] **x** while engulfed — *"You can't see anything!"*; no examine mode

## Input

- [ ] **Ctrl+Q** quits (gameplay, examine, vore modal)
- [ ] **Escape** alone does not quit
- [ ] During vore modal, **Escape** is no-op; **Ctrl+Q** quits

## Faction / swap (automated + optional dev shell)

Good and neutral NPCs are not in normal spawn. Automated tests cover faction AI and player swap.

Optional knight spawn:

```bash
python -c "from src.engine import GameEngine; from src.components import Alignment, Position; from src.systems.ai import spawn_test_npc; e=GameEngine(); p=e.player; pos=p.components[Position]; spawn_test_npc(e.world, x=pos.x+1, y=pos.y, species='knight', alignment=Alignment.GOOD); print('knight at', pos.x+1, pos.y)"
```

- [ ] Bump good/neutral → swap, no damage, swapped NPC skips once (when knight present)
- [ ] Bump evil wolf → normal attack

## Regression

- [ ] Vore modal, engulf, struggle, mercy, **F2** weaken
- [ ] Wait/regen, stunned movement, potions while stunned
- [ ] **R** new game, **S** debug stun
- [ ] Inventory **a–w**, **y–z** (slot **x** is examine)

**Pass criteria:** All items behave per `openspec/specs/enhancements-2/spec.md`; pytest green.