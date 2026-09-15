# Tasks: ai-personality-fuzzy

**Battle Sport batch:** implement only after whole-batch authorization (`../battle-pace-program/BATTLE_SPORT_SPEC.md`). Design frozen in `design.md` (2026-08-10). Includes **enemy and ally** fuzzy AI, orders, morale, crisis help.

**Hard deps in batch order:** weapon-measure + player-combat-commands (footwork + measure attacks) before AI phase.

## Setup (design)

- [x] Write `design.md` (final attr list, candidate intents, orders, morale, noise)
- [x] Designer accept design (freeze)

## PR A1 — Attribute schema

- [x] 1–10 attrs on entities; ranges; spawn roll
- [x] Targeted tests + manual checklist (batch OK 2026-08-10)

## PR A2 — Candidate intents

- [x] AI may choose existing player-parity actions (footwork, measure attack, etc.)
- [x] Targeted tests + manual checklist (batch OK 2026-08-10)

## PR A3 — Fuzzy scorer

- [x] Geometry fitness (weapon measure) + attr weights + noise
- [x] JSON-driven weights
- [x] Targeted tests + manual checklist (batch OK 2026-08-10)

## PR A4 — Content ranges

- [x] Current foes get personality ranges; bosses pin values if needed
- [x] Targeted tests + manual checklist (batch OK 2026-08-10)

## PR A5 — Playtest tune

- [x] JSON tuning from designer feedback
- [x] Designer sign-off for module (batch 2026-08-10)
