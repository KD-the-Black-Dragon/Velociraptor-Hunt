# Manual checklist — PR2 (entities.json validation + lazy spawn)

Run game: `python -m src.main`

Automated: `pytest tests/test_entity_validation.py tests/test_spawn_lazy_registry.py tests/test_entity_validation_startup.py -q`

## Valid startup

- [ ] Game launches normally with stock `data/entities.json`
- [ ] No traceback on startup

## Broken entities.json (manual)

Backup `data/entities.json`, then introduce a hard error (e.g. delete a required field or duplicate an id). Run `python -m src.main`.

- [ ] Dialog appears: **"Unable to start the game due to JSON error."** plus scrollable detail
- [ ] stderr shows same heading + plain-English detail (filename, Entity/Problem lines)
- [ ] `{user_data}/logs/startup_error.log` appended with timestamp (e.g. `7/6/2026 9:56 AM`) and full message
- [ ] Second failure appends to same `startup_error.log` (does not overwrite)
- [ ] **No** Python traceback on the user-facing path
- [ ] Exit code non-zero; game window does not open
- [ ] Session log under `{user_data}/logs/` exists but does **not** end with `Quit`
- [ ] Restore `entities.json` after test

## Soft warnings unchanged

- [ ] Unknown ability on an entity still loads (warn-and-ignore) — optional if you have a test mod entity

## Regression

- [ ] Normal play: new game, descend, combat unchanged after lazy spawn