# Tasks: weapon-measure

**Battle Sport batch:** implement only after designer authorizes the **whole batch** (see `../battle-pace-program/BATTLE_SPORT_SPEC.md`). Design is frozen in `design.md`.

Program map: `../battle-pace-program/ROADMAP.md`.

## Setup (design)

- [x] Write `design.md` (bands, geometry, seed weapons, JSON shape, open numbers)
- [x] Designer accept design (2026-08-10 freeze)
- [x] PR checklists below match design

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
