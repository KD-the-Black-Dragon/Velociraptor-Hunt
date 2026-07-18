# Proposal: ready-actions

## Problem

Numpad 5 currently pushes defensive balance hard (turtle dump). The designer wants two distinct stand-ready fantasies: **keep watch** (near-neutral) vs **raise shield / timid brace**.

## Solution

Open **`ready-actions`**: re-specify wait (5), brace (`d`), and slight step aggression as action-driven balance deltas—not stance toggles.

## Scope

### In

- Numpad 5 = keep watch / stand ready (tiny defensive from inactivity only)
- `d` = brace / hide behind shield (clear defensive commitment)
- Normal step = very slight aggressive lean
- JSON-tuned deltas; log lines via messages system

### Out

- Footwork (`f`), directed pokes, momentum, AI

## Dependencies

- **Requires:** foundation balance meter
- **Parallel-OK with:** weapon-measure
- **Recommended before:** calling player-combat-commands complete

## Program

See `openspec/changes/battle-pace-program/ROADMAP.md` (module **BP-R**).
