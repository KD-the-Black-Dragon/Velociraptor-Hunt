# Design: ready-actions (BP-R)

| Field | Value |
|-------|--------|
| **Module** | `ready-actions` |
| **Program** | `../battle-pace-program/BATTLE_SPORT_SPEC.md` |
| **Status** | Design frozen 2026-08-10 — implement only after whole-batch authorization |
| **Depends on** | Foundation balance meter |
| **Parallel OK** | With weapon-measure |

---

## Problem

Numpad 5 / wait currently behaves like a strong turtle dump. Design needs **two** stand-ready fantasies: neutral **keep watch** vs committed **brace**.

---

## Requirements

### Key binding

| Input | Action |
|-------|--------|
| **`.`** | Keep watch / stand ready |
| **Numpad 5** | **Same command** as `.` |
| **`d`** | Brace / raise guard |
| Normal step | Movement; **very slight** aggressive balance lean |

No stance-toggle UI — only action-driven balance deltas.

### Keep watch (`.` / 5)

- Near-**neutral** balance effect.
- Tiny defensive lean only from inactivity if data requires — **must not** create a fortress when spammed.
- AUT cost from JSON (legacy wait AUT may be reused or split).
- Log: calm “keep watch” style line via `messages.py`.

### Brace (`d`)

- Real **defensive commitment**: clear defensive balance delta + defensive actual-stat lean (JSON).
- Distinct from keep watch.
- Log: “raise guard” / brace style via `messages.py`.

### Step lean

- `balance_on_step` (or maneuver) = **very slight** aggressive (JSON; may already be 0 — retune to slight + if needed).

### AI parity

- Enemy and ally AI may select **keep watch** and **brace** as candidate intents (wired in ai-personality-fuzzy).
- Ferocity 0 style heavily prefers watch/brace (see AI design).

### Out of scope

- Footwork, directed attack, momentum, AI scoring (other modules)

---

## Data

Maneuver / balance keys in `data/match_combat.json` (or split file):

- `keep_watch` (or retarget `wait`) balance_delta ≈ 0 or tiny defensive
- `brace` balance_delta clearly defensive + any AC/evade lean hooks
- step balance_delta slight aggressive

---

## Acceptance

- Spamming 5 / `.` does **not** dump fighter to −10 fortress.
- `d` is the timid/shield commitment the player can feel.
- `.` and Numpad 5 are identical.
