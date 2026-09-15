# Proposal: Balance difficulty analyzer (hybrid simulator)

| Field | Value |
|-------|-------|
| **Date** | 2026-07-11 |
| **Status** | **Active** — design approved; awaiting implementation authorization |
| **Change** | `add-balance-simulator` |
| **Supersedes** | `openspec/changes/deferred-add-balance-simulator/` (headless bot + depth-only metrics) |
| **Spec targets** | New `openspec/specs/balance-simulator/spec.md`; light cross-reference in `balance` |

---

## Why

Balance tuning today relies on manual playtesting. The designer needs a **repeatable sanity check** after every tweak to `depth_scaling.json`, spawn weights, loot tables, and prefix rates — especially to catch:

- Floors that spike harder than the previous floor
- Deeper floors that are **easier** than shallower ones (difficulty ramp not keeping pace with player power)
- **High-variance** floors where one loot variable (e.g. weapon spawn) determines total victory vs total defeat

The tool must reflect **live stock `data/`** (no mods) and simulate layout/spawn/loot chaos — not a closed-form calculator.

---

## What

A **hybrid balance analyzer** with two passes in one CLI run:

1. **Trajectory pass (primary)** — Headless policy bot plays **full runs** from floor 1. For each floor 1–20 reached, record rich per-floor outcomes until a **time budget** expires.
2. **Isolation pass (secondary)** — For each floor 1–20, inject a **typical loadout** (derived from trajectory percentiles at floor entry) and simulate **only that floor** many times within the remaining time budget. Answers whether a floor is intrinsically nasty regardless of how the player got there.

### Outputs

- **Compare-sheet CSV** (Calc/Excel-friendly): fixed `metric` + `label` columns, **one column per run** for side-by-side diffs; optional wide curve file for charting.
- **Optional JSONL** per-run / per-floor events for deep inspection.
- **Adjustable timer** (`--seconds N`) instead of a fixed run count.

### Policy bot (instrument, not human mimic)

Reasonable play assumptions:

- Rest to full HP when rest is **reasonably** safe (not guaranteed — wanderers can interrupt).
- Use consumables **early** when a situation could become lethal.
- **Bail for stairs** when really bad; missing runes is acceptable and expected sometimes.
- On **stunned**: immediately quaff heal or teleport; treat failure as near-certain digestion.
- Avoid aquatic threats; do not charge sharks in water.
- No macguffin pursuit.

### Difficulty model

- **0** = collected all runes, weapon and armor improved vs floor entry, zero consumables spent, descended safely.
- **100** = digested on this floor every time.
- Middle outcomes weighted by sacrifice severity (digestion ≫ early bail ≫ consumables ≫ gear not improved). **Same upgrade penalty** whether a better item spawned and was missed or never spawned at all.

Export **all** component stats; composite `difficulty_score` is one derived column among many.

---

## Explicitly out of scope

- Graphical game loop (`python -m src.main`) or synthetic keyboard replay.
- Enabled mods — **stock `data/` only**.
- Macguffin victory metrics.
- Turn-count pressure (turns are not a difficulty axis).
- CI performance gating.
- Policy knobs in JSON (v1 thresholds live in Python; data-driven policy deferred).
- Human-perfect strategic play.

---

## Success

Designer runs:

```text
python tools/sim_balance.py --difficulty normal --seconds 300 --output balance_report.csv
```

and receives a CSV comparing floors 1–20 with:

- Trajectory difficulty curve + variance (p10/p50/p90)
- Isolation difficulty curve for the same floors
- Breakdown stats (digest rate, rune completion, consumables, gear improve rates, upgrade spawn/take diagnostics, conditional digest rates)
- Enough runs in the time budget to trust median trends on early floors; `runs_reached` column makes thin deep-floor data explicit

Re-running after a balance tweak and diffing CSVs in Excel shows whether the depth curve stayed smooth.