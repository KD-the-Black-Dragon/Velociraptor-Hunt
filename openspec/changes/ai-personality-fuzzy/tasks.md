# Tasks: ai-personality-fuzzy

**Battle Sport batch:** implement only after whole-batch authorization (`../battle-pace-program/BATTLE_SPORT_SPEC.md`). Design frozen in `design.md` (2026-08-10). Includes **enemy and ally** fuzzy AI, orders, morale, crisis help.

**Hard deps in batch order:** weapon-measure + player-combat-commands (footwork + measure attacks) before AI phase.

## Setup (design)

- [x] Write `design.md` (final attr list, candidate intents, orders, morale, noise)
- [x] Designer accept design (freeze)

## PR A1 — Attribute schema

- [ ] 1–10 attrs on entities; ranges; spawn roll
- [ ] Targeted tests + manual checklist

## PR A2 — Candidate intents

- [ ] AI may choose existing player-parity actions (footwork, measure attack, etc.)
- [ ] Targeted tests + manual checklist

## PR A3 — Fuzzy scorer

- [ ] Geometry fitness (weapon measure) + attr weights + noise
- [ ] JSON-driven weights
- [ ] Targeted tests + manual checklist

## PR A4 — Content ranges

- [ ] Current foes get personality ranges; bosses pin values if needed
- [ ] Targeted tests + manual checklist

## PR A5 — Playtest tune

- [ ] JSON tuning from designer feedback
- [ ] Designer sign-off for module
