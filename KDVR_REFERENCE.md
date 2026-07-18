# KDVR reference (for AI agents and contributors)

## What this file is

This repository **is Gladiavore**. It began as a clone of **K.D.'s Vore Roguelike (KDVR)**. The original KDVR project may also exist elsewhere as a separate install.

**KDVR-only code lives under `reference/kdvr/`**, not in product `src/` / `tests/` core.

## Product truth

| | **Gladiavore** (product) | **KDVR** (reference only) |
|--|--------------------------|---------------------------|
| Location | repo root (`src/`, `data/`, `tests/`, `openspec/changes/gladiavore-foundation/`) | `reference/kdvr/` |
| Loop | Career hub → curated arena matches | Multi-floor dungeon delve |
| Run | `python -m src.main` | not launched as the product |
| Specs | `openspec/specs/gladiavore-*` | historical under `reference/kdvr/openspec/` |

**Canonical design:** `openspec/changes/gladiavore-foundation/` — especially **`DESIGN_CANON.md`**.

## Harvest rules

1. Read product design first; do not re-add dungeon as New Game.
2. When you need a system (AI, inventory, FOV…), **copy from `reference/kdvr/` into product** and adapt — do not import `reference` at runtime.
3. Terminology: defeated / stunned / digested — never kill/die/death.
4. User data directory name: **Gladiavore**.

## Soft prune status

- Product App path is career-only (menu → name → background → hub → match).
- Dungeon engine, map gen, depth jump, macguffins, dungeon AI, sim, bulk KDVR tests: **moved to `reference/kdvr/`**.
- Some data loaders remain under product `src/data/` and `data/*.json` so mods/entity JSON still load; treat dungeon-only JSON as **inert content** until pruned further.

## Dual install warning

If both `kds-vore-roguelike` and `gladiavore` are editable installs sharing the `src` package name, Python may mix modules. Prefer:

```bash
pip uninstall kds-vore-roguelike -y
pip install -e ".[dev]"
```

when working on Gladiavore.
