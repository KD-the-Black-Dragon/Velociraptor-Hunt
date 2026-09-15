# Manual testing checklist — PR1 (depth scaling)

Run: `python -m src.main`

Stock `depth_scaling.json` is all-zero: **gameplay should match pre-PR1 feel.**

## Happy path

- [ ] New game starts; floor 1 enemies feel unchanged vs recent builds
- [ ] Descend a few floors; still no unexpected tankiness (stock Hard etc. also zero until PR5)
- [ ] Combat, vore, digestion still work
- [ ] No crash on summon abilities if any fire

## Edge / regression

- [ ] Good knights / neutrals unchanged relative to evils at same depth (both unbuffed on stock)
- [ ] Save/load still works (Fighter already persisted; no new save field this PR)
- [ ] Mods Options still opens (depth_scaling is whole-file replace; no fingerprint change)

## Performance

- [ ] Floor gen / turns feel normal (bake is once per NPC at spawn only)

## Automated

- [x] `python -m pytest tests/test_depth_scaling_pr1.py -v` (17 passed)
