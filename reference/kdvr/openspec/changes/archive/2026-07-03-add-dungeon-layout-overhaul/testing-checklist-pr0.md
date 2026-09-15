# Manual checklist — PR0 (sanity validation & regeneration)

Run: `python -m src.main`

## Sanity / regeneration

- [ ] Start **New Game** and descend (**Shift+.** on `>`) at least **10 times** — floors feel larger on average; no obvious “two tiny rooms + one corridor” layouts
- [ ] On each descent, all **three `>` stairs** feel well separated (not in a tight cluster)
- [ ] Watch **PowerShell** console — occasional `[map_gen] rejected attempt N: ...` lines are OK; sustained dozens per floor suggests thresholds too tight (report)
- [ ] (Optional) Temporarily break generation in dev — confirm **giant fallback room** appears instead of tiny chamber

## Regression

- [ ] Land still fully reachable from entrance
- [ ] Water lakes/rivers still appear on some floors
- [ ] **`.`** still waits; **Shift+.** still descends on stairs
- [ ] Good knight in LOS still follows downstairs

## Automated (agent runs before delivery)

- [ ] `pytest tests/test_dungeon_layout_pr0.py -q`
- [ ] `pytest tests/test_dungeon_pr2.py -q` (existing dungeon gen tests)