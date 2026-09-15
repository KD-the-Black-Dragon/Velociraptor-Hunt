# Proposal: Add Basic Vore Mechanics

## Why

Core roguelike v1 is shipped and archived. The core spec deliberately deferred vore to a separate domain. Players at low HP currently face only bump combat and stunned recovery — there is no predator pressure or engulfed-state gameplay that motivates the project's vore theme.

This change adds the first **vore domain** layer: probabilistic vore attempts when the player is weakened, modal narrative pacing, and an engulfed struggle loop with escape — without digestion or game-over in v1.

## What Changes

- Monster **vore attempt decisions** when player HP ≤ 50% max (progressive random chance; 100% at 0 HP)
- **Hit/miss resolution** with HP-scaled success; miss wastes the predator's turn
- **Center-screen multi-phase modal narrative** (dynamic phase queue; Enter to advance; modal text never copies to log; Escape quits)
- **Engulfed state**: co-tile with predator, blindness, struggle moves with escape chance + predator damage
- **Immunity**: engulfed player cannot be bump-attacked; co-tile bumps target the predator
- **Debug `F2`**: set all monster HP to 1 for struggle/defeat testing
- New spec: `openspec/specs/vore/spec.md`
- Narrative content types as **extensible string list** (OV / CV / AV in v1; equal-weight pick; all on by default until main menu)
- **Wolf proof-of-concept** spawn with multi-phase wolf narrative packs
- New modules: `src/systems/vore.py`, `src/vore_content.py`, plus ECS components and engine modal state

## Capabilities

### New Capabilities

- `vore` (spec + implementation): Vore attempts, modal UI, engulfed struggle, and modular boundary with core systems.

### Modified Capabilities

- `core-roguelike`: Update **Modular Vore Boundary** acceptance criterion and requirement wording to reflect behavioral modularity (`VORE_ENABLED`) rather than physical absence of vore code.

## Impact

**Touched areas**

- `src/engine.py` — modal state machine, input gating, RNG, struggle routing
- `src/systems/ai.py` — vore decision before chase, sorted iteration, predator freeze
- `src/systems/combat.py` — co-tile `_fighter_at` resolution
- `src/systems/render.py` — modal box, engulfed blindness
- `src/components.py`, `src/constants.py`, `src/messages.py`, `src/events.py`, `src/spawn.py`
- `tests/` — vore unit and acceptance tests

**Out of scope (v1 vore)**

- Digestion timers and player defeat via digestion
- Main menu content toggles (constants default all types on)
- Digestion damage and foreshadowing
- Inventory use while engulfed
- Predator movement while holding prey
- Stunned pass-turn module ("not enough energy to move" consumes turn)

## Success Criteria

1. All scenarios in `openspec/specs/vore/spec.md` pass automated or manual verification.
2. Core acceptance tests (`tests/test_acceptance.py`) continue to pass.
3. Incremental PR plan (8 PRs) is mergeable with tests at each phase.

## Design Reference

Full technical design: [`design.md`](design.md) (reviewed 2026-06-29; clarified post Enhancements 1 and user Q&A).