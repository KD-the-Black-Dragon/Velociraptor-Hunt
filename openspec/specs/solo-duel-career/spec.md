# Spec: Solo Duels career

## Purpose

Default campaign is **1-on-1 duels** with PC-only progression. Team/multi-opponent **Company** style remains in code but is not the New Game path.

## Requirements

### Campaign style

- Careers store `campaign_style`: `solo` or `company`.
- New Game creates **`solo`**.
- Missing style on load defaults to **`solo`** (pre-alpha).

### Solo hub

- No hire / assign team options.
- Starter ally picks skipped.
- `max_deployed_allies` is 0.

### Solo matches

- Match offers only cards with exactly one enemy and count 1.
- Spawn enforces a single opponent; no allies.

### Instant Action

- Card list for Ctrl+B is filtered to solo-eligible cards of the chosen green/red kind.

### Company freeze

- Roster, multi-enemy cards, and team hub paths remain available when `campaign_style` is `company` (tests / future re-enable). Not advertised on main menu.

## Terminology

defeated / stunned / digested.
