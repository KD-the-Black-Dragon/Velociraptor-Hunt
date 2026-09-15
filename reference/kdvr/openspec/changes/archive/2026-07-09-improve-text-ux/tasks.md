# Tasks: improve-text-ux

**Active PR:** *(none — change accepted and archived 2026-07-09)*  
**Font rule:** Digestion modal is the narrative model; inventory lists use the same dialog font.

---

## PR0 — OpenSpec bootstrap

- [x] `proposal.md`, `design.md`, `tasks.md` reviewed (decisions locked 2026-07-08)
- [x] `AGENTS.md` active change pointer
- [x] User authorizes PR1 coding

---

## PR1 — Placeholders + SCHEMA + new-game layout

- [x] Format `{predator}` on NPC→player vore attempt/success modal phases
- [x] Safe format (unknown keys left literal; no crash)
- [x] Tests for substitution; unknown key stays visible
- [x] SCHEMA: full markup category + alias list
- [x] New-game overwrite: lower band (like mod-mismatch), word-wrap, on-screen at min size
- [x] `testing-checklist-pr1.md`
- [x] Manual playtest sign-off (PR1 good; caution requirement added before PR2)

---

## PR2 — Witnessed NPC swallow/digest default **caution** color

- [x] On-screen NPC **vore hit/success** log lines use `MessageCategory.CAUTION` by default
- [x] On-screen NPC **digestion complete** log lines use `CAUTION` by default
- [x] Miss / fail vore lines **unchanged** (not forced caution)
- [x] Offscreen vore / offscreen digest lines **unchanged**
- [x] Tests: hit/digest in FOV → caution; miss and offscreen not forced caution
- [x] `testing-checklist-pr2.md`
- [x] Manual playtest sign-off (user authorized PR3)

---

## PR3 — Shared dialog chrome + other bare confirms

- [x] Shared panel chrome (fill + padding + simple border)
- [x] Apply to quit, mods-enter, macguffin victory, menu notices as needed
- [x] Clamp/wrap consistent with PR1 helper
- [x] Tests (render/smoke where practical) + checklist
- [x] Manual playtest sign-off (user authorized PR4)

---

## PR4 — Proportional font **trial** (digestion player modal)

- [x] Surface: **player digestion completion modal** only
- [x] Whole dialog log font (body + footers); CP437 fallback if font missing
- [x] Manual vet + tweaks (font +2, width 80%, top/side pad)
- [x] **Designer approval** of digestion modal as narrative model

---

## PR4b — Inventory full-pack design (pause)

- [x] Design notes in `design.md` §5b (multi-column preferred)
- [x] TEMP starter: 25 daggers + robes for `python -m src.main` (off under pytest)
- [x] Designer answers locked (dynamic cols, fill-down, wrap-in-cell, same rule for short lists, digestion font)
- [x] Designer playtests multi-column UI with full pack (sign-off before removing TEMP)

---

## PR5 — Narrative proportional rollout

- [x] Vore attempt/success modal (digestion model)
- [x] Examine description (digestion model)
- [x] Tests + `testing-checklist-pr5.md`
- [x] Manual playtest sign-off

---

## PR6 — Inventory / utilitarian multi-column + font

- [x] Multi-column list for 26 slots — locked design (§5b)
- [x] Apply to i / drop / wield / wear / quaff / evoke pick / ground pickup
- [x] Proportional present path (same digestion dialog font); CP437 fallback
- [x] TEMP full starter removed after sign-off
- [x] Tests + `testing-checklist-pr6.md`
- [x] Manual playtest sign-off

---

## PR7 — Remaining + acceptance

- [x] Sentence confirms / game-over body (title tile, body log font)
- [x] Tests + `testing-checklist-pr7.md`
- [x] Manual playtest sign-off (confirms, game over, progressive digestion haze)
- [x] Full suite `pytest tests/ -n 6`; re-run **only** failures if any
- [x] Spec update; archive; clear AGENTS pointer

---

## Out of scope

- [ ] ~~Help overlay~~
- [ ] ~~`{prey}` in player modals~~
- [ ] ~~Stock narrative rewrite~~
