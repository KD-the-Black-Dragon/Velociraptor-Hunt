# Manual testing checklist — PR4 (proportional digestion modal **trial**)

**How to run:** `python -m src.main`  
**Automated:** `python -m pytest tests/test_text_ux_pr4_digestion_font.py -n 6 -q`

## Automated (agent)

- [x] Digestion proportional image + skip-CP437 flag — passed

## Trial goal

Approve or reject the **look** of the player digestion completion modal in **log proportional font** (whole panel including “Press Enter” footer).

## Happy path

- [ ] Get digested by a wolf/shark (or force via play) → digestion modal phases use **smooth log font**, not tiles
- [ ] Panel has dark background + border; text wraps for long phases
- [ ] Footer **Press Enter** is readable; **Enter** advances phases
- [ ] Multi-phase sequences still work through to game over

## Fallback

- [ ] If font missing (optional): CP437 digestion modal still works (rename/hide TTF only if you want to verify)

## Regression

- [ ] Message log still proportional during play
- [ ] Vore modal still CP437 this PR (expected — rollout is PR5)
- [ ] Inventory / examine still CP437 this PR
- [ ] Min window: dialog stays usable

## Decision for PR5

- [ ] **Approve** trial look → proceed PR5 rollout  
- [ ] **Request tweaks** (size, padding, width, footer) before rollout  

## Out of scope this PR

- Vore, inventory, examine, game over proportional (PR5)
