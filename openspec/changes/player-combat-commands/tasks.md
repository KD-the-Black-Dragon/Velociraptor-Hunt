# Tasks: player-combat-commands

**Battle Sport batch:** implement only after whole-batch authorization (`../battle-pace-program/BATTLE_SPORT_SPEC.md`). Design frozen in `design.md` (2026-08-10).

**Prerequisite:** `weapon-measure` for directed-attack work. Footwork may land after intent core; attack resolution waits on BP-W.

## Setup (design)

- [x] Write `design.md` (keymap, footwork legality, cone rules, feint effects, costs)
- [x] Designer accept design (freeze)

## PR P1 — Intent resolver core

- [x] Shared optimistic intent API; no-op policy; cone target selection
- [x] Targeted tests + manual checklist (batch OK 2026-08-10)

## PR P2 — Footwork

- [x] `f` targeting; Chebyshev 1–2; costs; compound; Esc cancel; Shift+dir 1-tile
- [x] Targeted tests + manual checklist (batch OK 2026-08-10)

## PR P3 — Directed basic attack + measure

- [x] Easy directed attack bind; weapon bands + attack delay live
- [x] Requires weapon-measure shipped
- [x] Targeted tests + manual checklist (batch OK 2026-08-10)

## PR P4 — Feint ladder

- [x] R3–4 feint / false lunge; R5+ no-op; no shame-swing
- [x] Targeted tests + manual checklist (batch OK 2026-08-10)

## PR P5 — Help + regression

- [x] Key help / messages polish; regression suite
- [x] Designer sign-off for module (batch 2026-08-10)
