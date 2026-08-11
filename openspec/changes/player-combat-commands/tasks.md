# Tasks: player-combat-commands

**Battle Sport batch:** implement only after whole-batch authorization (`../battle-pace-program/BATTLE_SPORT_SPEC.md`). Design frozen in `design.md` (2026-08-10).

**Prerequisite:** `weapon-measure` for directed-attack work. Footwork may land after intent core; attack resolution waits on BP-W.

## Setup (design)

- [x] Write `design.md` (keymap, footwork legality, cone rules, feint effects, costs)
- [x] Designer accept design (freeze)

## PR P1 — Intent resolver core

- [ ] Shared optimistic intent API; no-op policy; cone target selection
- [ ] Targeted tests + manual checklist

## PR P2 — Footwork

- [ ] `f` targeting; 2-straight + knight; costs; compound; Esc cancel
- [ ] Targeted tests + manual checklist

## PR P3 — Directed basic attack + measure

- [ ] Easy directed attack bind; weapon bands + attack delay live
- [ ] Requires weapon-measure shipped
- [ ] Targeted tests + manual checklist

## PR P4 — Feint ladder

- [ ] R3–4 feint / false lunge; R5+ no-op; no shame-swing
- [ ] Targeted tests + manual checklist

## PR P5 — Help + regression

- [ ] Key help / messages polish; regression suite
- [ ] Designer sign-off for module
