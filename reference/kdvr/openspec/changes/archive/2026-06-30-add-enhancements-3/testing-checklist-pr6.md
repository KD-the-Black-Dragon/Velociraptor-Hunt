# PR 6 Manual Testing Checklist — Rescue and Integration

Run `python -m src.main` from the project root.

---

## Automated gate

```bash
python -m pytest tests/test_enhancements_3.py -v
python -m pytest tests/test_vore_ai.py tests/test_vore_engulfed.py -q
python -m pytest tests/ -q
```

All tests should pass.

---

## NPC rescue (defeat predator)

Use **F2** to weaken the wolf if needed. Get a wolf to engulf a stunned knight or rabbit (wait for off-screen vore or set up adjacency).

- [ ] **Player** bump-attacks holding wolf to 0 HP → rabbit/knight is **freed** on an adjacent tile
- [ ] Log shows *"The rabbit is freed from the wolf."* (or knight variant) when visible
- [ ] Freed prey keeps **stunned** state if still at 0 HP
- [ ] **Knight** bump-attacks holding wolf → same rescue for engulfed ally

## Player vore regression

- [ ] Stunned player adjacent to wolf → **vore modal** still opens (unchanged)
- [ ] Knight defeating wolf while **player** is inside → player gets *"You escape from …"* message

## Integration regression

- [ ] Predator tile shows **wolf glyph** on **dark red** background while holding prey
- [ ] Engulfed prey glyph never shown
- [ ] NPC swap, AI priorities, visibility-gated logs from prior PRs unchanged

**Pass criteria:** Defeating a holding wolf frees NPC prey with log when visible; player vore modal intact; pytest green.