# PR2 — Wander manual checklist

Run: `python -m src.main`

## Wander temperament (mindless evil — spore / living fire)

- [ ] Temporarily add `"Wander"` to an evil (mod) — loads without warning
- [ ] Wander evil **does not target or pursue** player even when visible — drifts/explores
- [ ] Wander evil still deals **bump damage** if it walks into a target
- [ ] **Not** for rabbits — stock rabbit has no `Wander`

## Unchanged behaviors

- [ ] Wander entity adjacent to hostile may still **bump attack** if movement brings contact
- [ ] `PreferVore` / vore / `SummonN` still fire when legal (not blocked by Wander)
- [ ] Stock rabbit without `Wander` unchanged if not assigned yet

## Regression

- [ ] Normal wolf still chases player
- [ ] Erratic bat (no Wander) unchanged

## Automated

- [ ] `python -m pytest tests/test_npc_abilities_wander.py tests/test_npc_abilities_erratic.py -v`