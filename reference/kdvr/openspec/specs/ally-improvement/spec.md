# ally-improvement Specification

## Purpose

**Ally improvement** adds personality and smarter rescue behavior for **good** allies: runtime name introductions, priority attacks on predators engulfing the player, and gratitude when the player frees good prey.

**Terminology:** defeated, stunned, digested — no kill/die/death.

**Depends on:** `enhancements-2` (naming), `enhancements-3` (good AI, NPC rescue), `npc-data` (entity data), `vore` / `digestion` (engulf, release).

## Requirements

### Requirement: Good Ally Name Introduction

Good NPCs without a `ProperName` SHALL introduce themselves **once per entity per run** when all hold:

- Good alignment
- Chebyshev-adjacent to the player
- Not stunned
- Player not engulfed
- No evil visible in **player FOV** (`game_map.visible`)
- No evil in the good entity's line of sight
- Entity has a non-empty name pool in `data/names.json` **and** non-empty `introduction` lines in `entities.json`

The game SHALL assign `ProperName` from `names.json` (keyed by entity id), pick a random `introduction` template, substitute `{name}`, and log the line when the good entity is in player FOV. Introduction log color SHALL come from optional `introduction_log_category` in `entities.json` (stock knight: `speech` / white). Introduction strings MAY also use inline `[[category]]...[[/]]` log markup.

Introductions run once per consumed player turn after `_update_fov()` and before the world phase (`try_good_introductions()`).

#### Scenario: Knight introduces when coast is clear

- GIVEN a good knight adjacent to the player
- AND no evil is visible to the player or the knight
- WHEN the player consumes a turn
- THEN a introduction line appears in the log (if knight in FOV)
- AND subsequent logs use the assigned proper name

#### Scenario: Introduction blocked by visible evil

- GIVEN a good knight adjacent to the player
- AND an evil NPC is visible to the player or the knight
- WHEN the player consumes a turn
- THEN no introduction occurs

### Requirement: Player-Engulfed Rescue Priority

While the player is engulfed, every good NPC with line of sight to the predator holding the player SHALL treat that predator as its **top-priority** attack target in `pick_good_chase()`, above other visible evil, follow, memory, and explore.

When the player is no longer engulfed, or the predator is not in line of sight, good AI SHALL use the default priority from `enhancements-3`.

#### Scenario: Knight prioritizes holding predator

- GIVEN the player is engulfed by a wolf
- AND a good knight has line of sight to that wolf
- AND another evil wolf is visible and closer
- WHEN the knight acts
- THEN it targets the engulfing wolf

### Requirement: Player Rescue Gratitude

When the **player** defeats an evil predator holding **good** prey, the game SHALL log the existing freed message **and** an additional gratitude line from `data/rescue_gratitude.json` with `{name}` replaced by the prey log name (`ProperName` if set, else species with article rules).

Gratitude SHALL apply to player bump attacks and wand attacks. NPC rescuers (e.g. knight frees knight) SHALL NOT emit gratitude. **Neutral** prey (e.g. rabbit) SHALL receive the freed line only.

Both lines SHALL use the same FOV gate as `npc_freed_from_predator` (prey or predator visible to player).

#### Scenario: Player frees knight

- GIVEN a wolf holds an engulfed good knight
- WHEN the player defeats the wolf
- THEN the log reports the knight is freed
- AND a gratitude line naming the knight appears

#### Scenario: Knight frees ally

- GIVEN a wolf holds an engulfed good knight
- WHEN another knight defeats the wolf
- THEN only the freed message appears

#### Scenario: Player frees rabbit

- GIVEN a wolf holds an engulfed neutral rabbit
- WHEN the player defeats the wolf
- THEN only the freed message appears

## Technical notes (non-normative)

- `src/systems/ally_introduction.py`, `src/data/names.json`, `entities.json` `introduction`
- `src/systems/ai.py` — `pick_good_chase()` rescue branch
- `src/data/ally_content.py`, `data/rescue_gratitude.json`, `release_npc_engulfed(..., rescuer=)`
- Come here! shout: `openspec/specs/command-allies/spec.md` (Follow/Attack draft superseded)