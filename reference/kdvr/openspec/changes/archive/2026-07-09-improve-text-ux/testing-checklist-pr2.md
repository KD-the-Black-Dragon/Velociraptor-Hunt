# Manual testing checklist — PR2 (caution for witnessed NPC swallow/digest)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_text_ux_pr2_caution.py -n 6 -q`

## Automated (agent)

- [x] Caution category tests — 5 passed

## Happy path

- [ ] In FOV, watch a wolf (or other evil) successfully vore a knight/rabbit → success line is **yellow/caution** (not grey)
- [ ] In FOV, watch digestion of that prey finish → digest-complete line is **caution**

## Out of scope (must stay non-caution default)

- [ ] In FOV, predator **fails** vore → miss line is **routine** (grey), not caution
- [ ] Far away (not in FOV): offscreen atmospheric vore/digest if it appears → **not** caution yellow

## Regression

- [ ] Player engulfed by NPC still uses vore modal (unchanged)
- [ ] Combat / speech colors still look normal

## Out of scope this PR

- Dialog chrome (PR3)
- Proportional fonts (PR4+)
