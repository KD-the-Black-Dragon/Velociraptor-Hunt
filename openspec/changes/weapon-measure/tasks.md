# Tasks: weapon-measure

**Do not implement any PR until the designer authorizes that PR by name.**

Design artifacts: complete `design.md` before W1 auth. Program map: `../battle-pace-program/ROADMAP.md`.

## Setup (design)

- [ ] Write `design.md` (bands, geometry, seed weapons, JSON shape, open numbers)
- [ ] Designer accept design
- [ ] PR checklists below match design

## PR W1 — Schema + geometry

- [ ] Weapon JSON schema: attack_delay, measure bands
- [ ] Loader validation
- [ ] Range-band geometry helper (incl. knight as band-2 where specified)
- [ ] Targeted tests
- [ ] Manual checklist (data/dev-facing OK)

## PR W2 — Resolution wire-up

- [ ] Basic attacks use weapon attack_delay as AUT
- [ ] Band effectiveness applied in resolution
- [ ] Targeted tests
- [ ] Manual checklist

## PR W3 — Seed content + polish

- [ ] Sword / spear / heavy / short blade measure curves
- [ ] Examine or UI hint if cheap
- [ ] Targeted tests
- [ ] Designer sign-off for module
