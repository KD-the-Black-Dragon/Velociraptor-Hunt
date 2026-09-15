# Manual checklist — PR2 (Tier A BFS caching)

Run: `python -m src.main`

## Performance (subjective)

- [ ] Move 20+ turns on a normal floor — turns resolve without noticeable delay
- [ ] No multi-second stalls after each keypress (compare to pre-PR2 if possible)

## Behavior unchanged (regression)

- [ ] Wolf chases player around a corner (break LOS, memory pursuit still works)
- [ ] After chase give-up, wolves eventually disperse from a closed door (near player)
- [ ] Neutral rabbits wander without freezing near player
- [ ] Good ally introductions still fire when adjacent and safe

## Headless benchmark (optional)

```bash
python tools/profile_turn.py --scenario default --action consume --iterations 30
```

PR2 baseline: mean ~77 ms, p95 ~92 ms (seed 42).