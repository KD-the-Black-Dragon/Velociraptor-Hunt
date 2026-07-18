# Overnight batch status

**Started:** 2026-07-12 ~00:32 UTC (PID 18144)  
**Last checked:** placement phase in progress (~60–90 s/seed)

## Early findings (partial)

| Seed | runes_on_map | Notes |
|------|--------------|-------|
| 1 | 3 | Viable |
| 2 | 0 | Placement fallback — skip for rune tests |
| 3 | 0 | Placement fallback |
| 4 | 0 | Placement fallback |

**Pre-scan spot check (easy, 8000 turns):** seed **200** → depth **4**, runes **14** (strong integration candidate).

## Jobs launched

| Job | Command | Output |
|-----|---------|--------|
| Seed scan | `python -u tools/seed_scan_overnight.py` | `balance_seed_scan.csv`, `.log`, `_summary.txt` |

## Phases (in order)

1. **Placement** — seeds 1–100: count floor runes spawned vs quota
2. **Normal sim** — viable seeds 1–100, 5000 turns each
3. **Easy sim** — viable seeds 1–60, 8000 turns each
4. **Deep follow-up** — any seed that collected ≥1 rune or reached depth ≥2: 12000 turns normal + easy

## PR2 code fixes (already in tree)

- `first_step_toward` uses BFS distances **from goal** (not from player)
- Policy **WAIT** + activate when standing on visible rune tile
- Integration test: easy seed 4242 collects ≥1 rune (21/21 sim tests pass)

## When you return

1. Read `balance_seed_scan_summary.txt` for best seeds
2. Tail `balance_seed_scan.log` if still running
3. Open `balance_seed_scan.csv` in Calc/Excel for full data

## Expected runtime

| Phase | Estimate |
|-------|----------|
| Placement ×100 | ~2 h |
| Normal sim × viable | ~3–4 h |
| Easy sim × viable ≤60 | ~2–3 h |
| Deep follow-up | ~1–2 h |
| **Total** | **~8–10 h** |

Partial CSV rows are flushed after each seed. If `balance_seed_scan.log` timestamp is stale for >15 min, check PID 18144 in Task Manager.