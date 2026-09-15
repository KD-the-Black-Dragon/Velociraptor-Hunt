# Lineage and harvest (for AI agents and contributors)

## What this file is

This repository **is Velociraptor Hunt**. The folder began as a **copy of
Gladiavore**, which began as a clone of **K.D.'s Vore Roguelike (KDVR)**.

**Gladiavore and KDVR originals live in other folders.** Do not treat this tree
as those games. Do not try to “keep Gladiavore working” as the product.

KDVR-only dungeon modules in this copy live under `reference/kdvr/`, not as
product runtime.

## Product truth

| | **Velociraptor Hunt** (product) | **Gladiavore** (donor snapshot) | **KDVR** (reference only) |
|--|--------------------------------|---------------------------------|---------------------------|
| Location | this repo’s design + future hunt `src/` | current `src/`, `data/`, Gladiavore OpenSpec | `reference/kdvr/` |
| Loop | One hunt: hunter vs velociraptor | Career hub → arena matches | Multi-floor dungeon delve |
| Run | `python -m src.main` (donor until hunt lands) | not the product | not the product |
| Specs | `openspec/changes/archive/2026-09-04-velociraptor-hunt/` | historical in this copy | historical under `reference/kdvr/openspec/` |

**Canonical design:** `openspec/changes/archive/2026-09-04-velociraptor-hunt/` — especially
**`DESIGN_CANON.md`**. Gladiavore’s `DESIGN_CANON.md` is donor history.

## Harvest rules

1. Read hunt design first. Do not re-add a career hub or a dungeon as New Game.
2. When you need a system (AI, FOV, inventory, weather hooks, vore, save codec),
   **copy from this tree’s donor `src/` or `reference/kdvr/`** and adapt — do not
   import `reference` at runtime, and do not edit the original Gladiavore/KDVR
   folders.
3. Terminology: defeated / stunned / digested (devoured) — never kill/die/death.
4. User data directory name (target): **Velociraptor Hunt**.

## What the snapshot still contains

- Gladiavore App path (menu → name → background → hub → match) is still the
  running donor loop.
- KDVR dungeon engine, map gen, and bulk dungeon tests: under `reference/kdvr/`.
- Some data loaders remain under product `src/data/` and `data/*.json` so the
  donor still loads; treat Gladiavore/KDVR JSON as **inert** for the hunt until
  replaced.

## Dual / triple install warning

If `kds-vore-roguelike`, `gladiavore`, and this hunt tree are all editable
installs sharing the `src` package name, Python may mix modules. Prefer a
**single** editable install of **this** folder when working on Velociraptor Hunt:

```bash
pip uninstall kds-vore-roguelike gladiavore -y
pip install -e ".[dev]"
```
