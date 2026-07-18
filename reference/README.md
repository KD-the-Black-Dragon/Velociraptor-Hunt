# Reference material (not product runtime)

This folder holds **KDVR (K.D.'s Vore Roguelike) lineage** kept for **harvest**, not as the running game.

| Path | Contents |
|------|----------|
| `kdvr/` | Dungeon crawler modules, tests, data, and historical OpenSpec specs/changes moved out of product core |

## Product vs reference

| | Product (repo root) | Reference |
|--|---------------------|-----------|
| Loop | Career hub → arena matches | Multi-floor dungeon delve |
| Import path | `src.*` | **Do not** put on `PYTHONPATH` for the game |
| Purpose | Ship Gladiavore | Copy/adapt code into product when a module needs it |

## How to harvest

1. Browse `reference/kdvr/src/...` for patterns (AI, inventory, FOV, save codec, etc.).
2. **Copy** the useful bits into product `src/` (or a new package) and adapt for arena/career fiction.
3. Do **not** `from reference...` import in product code — keep product import graph clean.
4. Prefer Gladiavore design in `openspec/changes/gladiavore-foundation/` over KDVR specs under `reference/kdvr/openspec/`.

## Layout under `kdvr/`

```
kdvr/
  src/           # former product modules (engine, map_gen, systems/ai, sim, …)
  tests/         # former dungeon/system tests
  data/          # dungeon JSON still useful as examples (also mirrored stubs in product data/ where loaders require files)
  openspec/      # historical specs + balance-pass change
```

## Note on dual editable installs

If both `kds-vore-roguelike` and `gladiavore` are installed editable and both use the package name `src`, Python can mix modules from two trees. Prefer a single editable install of **gladiavore** when working on this repo:

```bash
pip uninstall kds-vore-roguelike -y
pip install -e ".[dev]"
```
