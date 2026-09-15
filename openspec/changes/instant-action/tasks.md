# Tasks: instant-action

**Do not implement any PR until the designer authorizes that PR by name.**

---

## Setup (design)

- [x] Create change folder
- [x] Two-phase kind + match-card id design (designer feedback)
- [x] Designer authorize whole batch (implement)

---

## PR IA1 — Two-phase entry UI

- [x] Phase A: Green (1) / Red (2); Esc → menu
- [x] Phase B: type **match card id**; dynamic list from `match_cards.json` filtered by kind + buffer
- [x] Esc on Phase B → Phase A
- [x] Validation messages; Ctrl+B no longer crashes
- [x] Targeted tests + manual checklist

---

## PR IA2 — Solo match from card

- [x] Resolve card → enemies; sand pit; solo; static loadout
- [x] Kind from Phase A; force max_allies 0
- [x] Instant isolation (no autosave/career write)
- [x] Targeted tests + manual checklist

---

## PR IA3 — Exit + polish

- [x] All end paths → main menu recap footer
- [x] Ctrl+S soft no-save
- [x] Live spec + designer sign-off (2026-08-10 manual OK)

---

## Out of scope

- Freeform entity syntax, loadout UI, allies, hallway map, sim CLI
