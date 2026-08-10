# Tasks: grapple-swallow-modals

**Do not implement any PR until the designer authorizes that PR by name.**

---

## Setup (design)

- [x] Create `proposal.md`, `design.md`, `tasks.md`
- [x] Record designer intent (modals + 1% swallow escape + struggle/conserve)
- [x] Designer: grapple is stub pending revamp
- [x] Authorize PR1 + PR2 (2026-08-04)

---

## PR1 — Grapple red modal + swallow math fix

**Auth:** authorized 2026-08-04 (batch with PR2).

### Checklist

- [x] PC grapple: red low-right modal; `{PredatorName} grapples you!`; options 1/2/.
- [x] Remove duplicate grapple control block from status when PC-held
- [x] `swallow_struggle_escape_chance` (0.01) in `match_vore.json` + loader
- [x] Swallow thrash/struggle uses **1%**, not `break_away * 0.35`
- [x] Ally swallow auto-break uses same rare chance
- [x] Messages via `messages.py` where new
- [x] Spec + DESIGN_CANON touch
- [x] Targeted tests

---

## PR2 — Swallow large interactive modal + conserve strength

**Auth:** authorized 2026-08-04.

### Checklist

- [x] Large interface-blocking swallow present (haze + panel)
- [x] Interactive only: `1` struggle, `2` conserve (no free direction thrash)
- [x] Narrative stub lines (JSON) by phase index
- [x] `conserved_strength` on `GrappleState`; apply to digest endurance
- [x] Footer/keys aligned
- [x] Targeted tests + manual checklist
- [x] Designer manual sign-off (checklist verified; post-playtest polish: modal size, tile colors, clinch tiles, uncapped conserve, no Ctrl+Q)

---

## Deferred

- Full Wrestling revamp (designer: grapple is stub)
- Deep swallow/engulf prose library
- Full ENGULFED cinematic modal

---

## Acceptance

- [x] PR1–PR2 + playtest polish accepted by designer
- [ ] Archive change (optional; when designer wants it closed)
