# Tasks: weapon-measure

**Battle Sport batch:** implement only after designer authorizes the **whole batch** (see `../battle-pace-program/BATTLE_SPORT_SPEC.md`). Design is frozen in `design.md`.

Program map: `../battle-pace-program/ROADMAP.md`.

## Setup (design)

- [x] Write `design.md` (bands, geometry, seed weapons, JSON shape, open numbers)
- [x] Designer accept design (2026-08-10 freeze)
- [x] PR checklists below match design

## PR W1 — Schema + geometry

- [x] Weapon JSON schema: attack_delay, measure bands
- [x] Loader validation
- [x] Range-band geometry helper (incl. knight as band-2 where specified)
- [x] Targeted tests
- [x] Manual checklist (batch end — designer OK 2026-08-10)

## PR W2 — Resolution wire-up

- [x] Basic attacks use weapon attack_delay as AUT
- [x] Band effectiveness applied in resolution
- [x] Targeted tests
- [x] Manual checklist (batch end — designer OK 2026-08-10)

## PR W3 — Seed content + polish

- [x] Sword / spear / heavy / short blade measure curves
- [x] Examine or UI hint if cheap
- [x] Targeted tests
- [x] Designer sign-off for module (batch end — 2026-08-10)
