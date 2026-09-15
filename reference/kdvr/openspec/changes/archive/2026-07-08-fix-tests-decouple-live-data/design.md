# Design: Decouple tests from live data

## Policy

1. **Never** assert exact live balance: HP, damage, accuracy, spawn weights, density, macguffin depths, narrative phrases from stock files.
2. **May** smoke-load live paths: file exists, parses, `schema_version` present, registry non-empty.
3. **Must** pin content for behavior tests via inline dicts, `tmp_path` JSON, or `tests/*_test_helpers`.

## Category A — delete or demote to smoke

| Area | Action |
|------|--------|
| `test_npc_data_pr1` golden entity set / wolf field snapshots | Smoke only: loads, has ids, schema_version |
| `test_npc_data_pr2` live accuracy/damage equals | Delete golden asserts; keep pure combat math with synthetic fighters |
| `test_npc_data_pr3` live narrative snippets | Fixture narratives on definitions |
| `test_dungeon_spawn_config` default path golden bands | Smoke load only; keep parse/inherit tests with inline config |
| `test_macguffins_pr1` stock depths/names/eligibility | Smoke load; keep parse/validation on `_minimal_macguffins_payload` |
| `test_enhancements_3::test_wolf_outdamages_knight_at_spawn` | Delete |
| Offscreen/digest/vore phrase pins on stock pools | Fixture entity messages or assert non-empty log line of expected category |

## Category B — rewrite

| Area | Approach |
|------|----------|
| Lifedrain | Synthetic fighters / spawn_test_npc with fixed HP; optional ability attach |
| Macguffin spawn PR2 depth tests | Inject fixture registry with known depth bands |
| Vore constants phase helper | Pass inline narrative tuples, not stock wolf |
| Ally introduction if needed | Fixture entity registry with introduction fields |

## Category C — contract

| Area | Approach |
|------|----------|
| `test_spawn_lazy_registry` | Match current lazy `WOLF_RENDERABLE` / `_get_registry` API |
| Erratic / render if still failing | Fix test setup, not data files |

## PR plan

### PR1 (this implementation)

Single PR: A deletes/smoke + B rewrites for known failures + C spawn lazy fix. Full suite re-run.

No multi-PR split needed — pure test hygiene.
