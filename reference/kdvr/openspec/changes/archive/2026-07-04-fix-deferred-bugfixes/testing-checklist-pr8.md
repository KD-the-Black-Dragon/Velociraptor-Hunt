# Manual checklist — PR8 (narrative capitalization)

Run: `python -m src.main`

## NPC vore log (on-screen)

- [ ] Trigger a visible wolf NPC vore hit on a stunned knight; log line starts with **The wolf** (not `the wolf`).
- [ ] If a line contains `. ` before another entity name, the name after the boundary is capitalized (e.g. `gone. The rabbit` style).

## Digestion log

- [ ] Let an NPC digestion complete on-screen; completion line starts with **The {predator}**.
- [ ] Lines using ` - ` (dash) do **not** capitalize the word after the dash (e.g. `triumphantly - the knight` stays lowercase after dash).

## Off-screen atmospheric lines

- [ ] With predator/prey off-screen, successful vore or digest still logs a line with proper **The** capitalization at sentence start.

## Player digestion modal

- [ ] When the player is digested, modal phases capitalize **The wolf** (or species name) at line start and after `.` `?` `!`.
- [ ] Phrases like **`- you.`** stay lowercase after the dash (dash is not sentence-ending punctuation).
- [ ] Multi-phase modals capitalize `{predator}` on later phases after sentence-ending punctuation when authored that way.

## Regression

- [ ] PR0–PR7 behavior intact (log colors, wrap, overlays, status corner runes).