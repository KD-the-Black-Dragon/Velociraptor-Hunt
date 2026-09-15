# Manual checklist — PR10 (neutral explore anti-stuck)

**Playtest sign-off:** Partial — ping-pong fixed; clustering and player-proximity freezes noted. Full explore fix tracked in `better-npc-exploration`.

Run: `python -m src.main`

## Explore oscillation

- [ ] Find a neutral rabbit (or other neutral) alone on the floor with no wolves in sight.
- [ ] Watch it explore for 20+ turns in a dead-end or narrow alcove — it should **not** ping-pong endlessly between two tiles.
- [ ] When boxed between recent tiles, the neutral **waits** a turn instead of reversing.

## Goal repick

- [ ] After repeating the same tile twice in a short window, the neutral picks a **new** explore goal (movement pattern changes).

## Regression

- [ ] Neutral **flee from evil** unchanged — rabbit still runs from visible wolves.
- [ ] Coward rabbit at full HP near wolf still uses baseline flee/explore rules (not broken by anti-stuck).
- [ ] PR9 pursuit momentum for good/evil still works.
- [ ] PR0–PR9 behavior intact.