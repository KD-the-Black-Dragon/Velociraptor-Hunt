# Tasks: player-combat-commands

**Do not implement any PR until the designer authorizes that PR by name.**

**Prerequisite:** `weapon-measure` accepted for P3+. Footwork P1–P2 may design/implement after intent core even if weapons still landing—attack PR waits on BP-W.

## Setup (design)

- [ ] Write `design.md` (keymap, footwork legality, cone rules, feint effects, costs)
- [ ] Designer accept design

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
