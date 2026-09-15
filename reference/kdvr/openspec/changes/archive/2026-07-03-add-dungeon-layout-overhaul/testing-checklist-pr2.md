# Manual checklist — PR2 (doors)

Run: `python -m src.main`

## Generation

- [ ] New floors show **`+`** glyphs at some corridor mouths (~half of junctions, not every tile)
- [ ] Closed doors block line of sight — stand on one side, confirm you cannot see through **`+`**

## Opening

- [ ] Walk into a closed door (**`+`**) — door becomes **`-`**, you **do not** enter the tile, **turn consumed**
- [ ] After opening, you can walk through **`-`** normally

## Closing

- [ ] Press **`c`** — log shows *"Close door — choose a direction."*
- [ ] Then press a direction toward an open door (**`-`**) — door becomes **`+`**, turn consumed
- [ ] **`c`** then direction toward a tile with no open door — *"There's no open door there."*, **no turn consumed**
- [ ] **`c`** toward open door with monster or item on it — *"There's something in the way."*, door stays open, **no turn consumed**
- [ ] Diagonal close works (e.g. **`c`** then numpad/vi diagonal key)
- [ ] Doors are **not** clustered in room corners; no **two `+` tiles touching**

## NPCs

- [ ] Wolf/monster on other side of closed door does not path through; does not open door
- [ ] After you open door, NPCs still do not pass (they cannot use doors)

## Regression

- [ ] PR0 spread + PR1 layouts still work
- [ ] Flyers (if visible) blocked by closed doors on land

## Automated

- [ ] `pytest tests/test_dungeon_layout_pr2.py -q`