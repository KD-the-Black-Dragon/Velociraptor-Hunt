# PR3 — Hands manual checklist

Run: `python -m src.main`

## Hands door behavior

- [ ] Add `"Hands"` to kobold or wolf via mod — loads without warning
- [ ] Hands NPC paths through closed door in explore/chase (BFS reachability)
- [ ] Hands NPC **steps onto** closed door → door becomes open; NPC occupies tile
- [ ] NPC **without** Hands still blocked by closed doors

## Logs (FOV-gated)

- [ ] See opener in FOV → *"{Name} opens the door."*
- [ ] See door only (opener off-screen) → *"Something opens the door."*
- [ ] Neither visible → no log line

## Regression

- [ ] Player `c` / bump-open door unchanged
- [ ] Door spite / memory pursuit door behavior on normal wolves unchanged

## Automated

- [ ] `python -m pytest tests/test_npc_abilities_hands.py tests/test_explore_reachable_goals.py::test_hands_stub_allows_closed_door_in_explore_bfs tests/test_dungeon_layout_pr2.py -v`