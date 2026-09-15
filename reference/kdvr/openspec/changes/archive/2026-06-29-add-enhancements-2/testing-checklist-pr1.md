# PR 1 Manual Testing Checklist — Identity Foundation

Run `python -m src.main` from the project root.

**Note:** Combat logs still say *"monster"* until PR 2. This PR adds data and helpers only.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_2.py tests/test_vore_constants.py::test_spawn_tags_wolf_vore_capable -v
python -m pytest tests/ -q
```

All tests should pass.

---

## Spawn and components (no visible UI change yet)

- [ ] `python -m src.main` starts without errors
- [ ] Wolves still appear and behave as before (chase, bump combat, vore when weakened)
- [ ] Gameplay is unchanged aside from internal naming data

## Fang (invisible until PR 2 combat logs)

Fang exists in data but combat still says *"monster"* for now. To verify Fang in a Python shell:

```bash
python -c "from src.engine import GameEngine; from src.components import ProperName, VoreCapable; e=GameEngine(); w=[m for m in e.world.Q.all_of(tags=[VoreCapable]) if m.components.get(ProperName)]; print(len(w), w[0].components[ProperName].name if w else None)"
```

- [ ] Output shows `1 Fang` (exactly one named wolf)

## Regression

- [ ] **F2** still weakens wolves
- [ ] Vore modal still works at 0 HP
- [ ] Wait/regen/stunned behavior unchanged
- [ ] **Escape** still quits (Ctrl+Q arrives in PR 6)

**Pass criteria:** No crashes; pytest green; Fang data present in spawn.