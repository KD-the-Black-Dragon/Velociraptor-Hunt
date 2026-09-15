# Reference material (not product runtime)

This folder holds **KDVR (K.D.'s Vore Roguelike)** lineage kept for **harvest**,
not as the running game.

This whole repository is a **copy of Gladiavore** used as donor code for
**Velociraptor Hunt**. The original Gladiavore and KDVR projects live in other
folders.

| Path | Contents |
|------|----------|
| `kdvr/` | Dungeon crawler modules, tests, data, and historical OpenSpec specs/changes |

## Product vs reference

| | Product (this repo) | Donor `src/` | `reference/kdvr/` |
|--|---------------------|--------------|-------------------|
| Loop (target) | One velociraptor hunt | Gladiavore career/match (current running snapshot) | Multi-floor dungeon delve |
| Import path | future hunt modules under `src.*` | current `src.*` | **Do not** put on `PYTHONPATH` for the game |
| Purpose | Ship Velociraptor Hunt | Copy/adapt engine pieces | Copy/adapt FOV, AI, vore, saves, etc. |

## How to harvest

1. Browse donor `src/` first (already a libtcod career/match game), then
   `reference/kdvr/src/` for dungeon-era systems.
2. **Copy** useful bits into hunt-oriented modules and adapt for park/hunt fiction.
3. Do **not** `from reference...` import in product code.
4. Prefer hunt design in `openspec/changes/archive/2026-09-04-velociraptor-hunt/` over Gladiavore or
   KDVR specs remaining in this copy.

## Dual editable installs

If `kds-vore-roguelike`, `gladiavore`, and this tree are all editable and share
the package name `src`, Python can mix modules. Prefer a single editable install
of **this** repo when working here:

```bash
pip uninstall kds-vore-roguelike gladiavore -y
pip install -e ".[dev]"
```
