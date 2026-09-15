# Acceptance: fix-tests-decouple-live-data

**Date:** 2026-07-08

## Before

Full suite: **~40 failed** — almost all pinned live `data/` balance (entity stats, spawn density, macguffin depths, narrative phrases, glyphs).

## After (hybrid)

| Action | Examples |
|--------|----------|
| **A smoke / delete** | Entity/macguffin/dungeon_spawn stock snapshots → smoke only; deleted wolf-vs-knight damage balance test |
| **B fixtures** | `fixture_macguffin_registry`, synthetic fighters for combat, non-empty log asserts for offscreen/digest |
| **C contract** | Spawn lazy registry; vore render uses live glyph from `Renderable`; ally intro checks name not `"I am "` |

## Full suite

```text
1124 passed, 112 warnings in ~24 min
```

**0 failures.**

## Policy reinforced

`tests/conftest.py` documents: no balance pins; smoke-only live loads; fixtures for behavior.
