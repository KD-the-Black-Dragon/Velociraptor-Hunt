# Spec: Gladiavore career loop

## Purpose

Career-mode product loop for **Gladiavore**: downtime hub between curated arena matches, gold/renown, roster, and run-ending only via PC digestion on red (typical).

## Requirements

### Career state

- Career persists outside install dir under product name **Gladiavore**.
- Fields include: player name, gold, renown, round index, difficulty, roster, injuries, starter gate, background id, last patron result.
- Missing optional save fields default on load (save compatibility).

### Downtime hub

- Abstract downtime menu between matches.
- Hire (tiers), assign deploy, heal injuries (gold steps), match select.
- Starter gate: free starter ally picks before other hub actions.

### Match cards

- Premade card catalog in JSON; hub offers up to **3** eligible cards per round.
- Green cards only on predefined green rounds (Easier difficulty may add more).
- Card carries kind (green|red), payout mult, max allies, enemy spawn list.

### Economy

- Win/loss/surrender payouts from JSON; green underpays vs red.
- Difficulty multiplies payouts (JSON tiers).
- Crowd may grant a small high-favor gold crumb (stub; no fine for low favor).

### Patrons

- Three named patrons; one sanity-checked objective per match.
- Hit → bonus gold; miss → note only (no penalty).

### Backgrounds

- Choice at new career after name entry; starting gold/renown stub only.
- Long-term victory goals deferred.

## Non-goals

- Full WWAATD patronage politics.
- Deep background end goals (stub only).
- Dungeon-crawl as primary product loop.
