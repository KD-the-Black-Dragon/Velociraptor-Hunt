# Design: Enhancements 3 — Faction Content and AI

## Current state (post–Enhancements 2)

| Area | Today |
|------|--------|
| Spawn | Evil wolves only (3–5) |
| AI | Chase visible hostiles; neutral flees evil; **idle** when nothing to do |
| 0 HP NPC | Removed — *"The wolf was defeated."* |
| Regen | Player only (+1 / 8 player turns) |
| Vore | Player target only; modal + engulf UI |
| Swap | Player → good/neutral only |

## Resolved decisions (2026-06-29)

| # | Decision |
|---|----------|
| 1 | **Knight** (good): cyan `k`. **Rabbit** (neutral): grey `r`. Placeholder examine text. |
| 2 | **Static spawn** for testing (fixed counts). Procedural population **deferred**. |
| 3 | **Good/neutral** stunned at 0 HP; never removed until digestion (deferred). **Evil** defeated at 0 HP. |
| 4 | **Regen:** good/neutral every **8** player turns; evil every **12** player turns (+1 HP, below max). |
| 5 | **Evil AI priority:** (1) fight good/player in LOS → (2) move to good/player last known → (3) fight neutral in LOS → (4) move to neutral last known → (5) explore random walkable tile. Higher priority **preempts** lower. |
| 6 | **Good AI:** (1) fight evil in LOS → (2) follow player in LOS → (3) player last known → (4) explore. **Ignore** neutral and other good NPCs as targets. Bump player = no-op + **console log only**. |
| 7 | **Neutral:** flee visible evil if **HP > 0**; stunned = no voluntary movement; else explore when quiet. |
| 8 | **Explore:** random walkable tile anywhere on map; on reach, pick another. |
| 9 | **Memory:** last-known per tier (evil: primary + neutral; good: evil + player); cleared when tile reached. |
| 10 | **NPC swap:** good↔good, good↔neutral, neutral↔neutral, evil↔evil on bump. **Only player** initiates swap with good/neutral. No NPC moves onto player tile. |
| 11 | **NPC vore:** evil only; log-only miss/hit lines from OV/CV/AV pools (prefs-filtered); **headless engulf** on hit. Digestion deferred. |
| 12 | **Rescue:** defeating a predator frees engulfed good/neutral prey (existing defeat cleanup + combat path). |

## Components

```python
@attrs.define
class AIState:
    """Per-NPC AI memory and exploration."""
    last_known_primary: Position | None = None   # evil: player/good
    last_known_neutral: Position | None = None   # evil only: neutral prey
    last_known_evil: Position | None = None      # good only: last seen evil
    last_known_player: Position | None = None    # good only: last seen player
    explore_goal: Position | None = None
```

Reuse `Stunned` tag for good/neutral NPCs at 0 HP (same semantics as player: no voluntary movement).

`VoreCapable` remains on **evil** spawns only.

## Spawn (v1 test layout)

Fixed counts per `new_game()` (tunable constants):

| Species | Alignment | Count | Glyph | Color |
|---------|-----------|-------|-------|-------|
| wolf | evil | 3 | `o` | (200, 80, 80) |
| knight | good | 2 | `k` | (120, 220, 255) cyan |
| rabbit | neutral | 3 | `r` | (140, 140, 140) grey |

Examine:

- Knight: *"A noble figure in medieval armor."*
- Rabbit: *"A small and harmless lagomorph."*

Placement: reuse `_candidate_tiles` shuffle; assign species in batch (not procedural weights).

## Combat and stunned

```text
on bump-attack defender at 0 HP:
  if defender alignment in (GOOD, NEUTRAL):
    hp = 0; add Stunned; log "The {name} is stunned!"
    do NOT clear entity
  elif defender alignment == EVIL:
    existing defeat + clear
```

Regen in `_apply_natural_regen` (player) extended to NPC loop:

- Good/neutral: if `player_turn_count % 8 == 0` and hp < max → +1; clear Stunned if hp > 0 → *"The {name} is no longer stunned."*
- Evil: if `player_turn_count % 12 == 0` and hp < max → +1

## AI priority (per turn)

```text
for each NPC (sorted, skip if Predator holding prey unless sync):
  if Stunned: skip voluntary action
  if skip_turn_set: continue

  update memory from current LOS

  intent = pick_intent(alignment)  # returns: flee | chase | explore_goal_pos

  if intent == flee: step away from nearest visible evil
  elif intent == chase: step toward target entity or last_known position
  elif intent == explore: step toward explore_goal; on reach, pick new goal

  try_action (move, swap, or attack)
```

### Evil `pick_intent`

1. Visible **good NPC or player** (combat hostile) → chase nearest (tie random)
2. Else `last_known_primary` set → move toward it (clear when reached)
3. Visible **neutral** → chase nearest neutral (for combat/vore opportunity)
4. Else `last_known_neutral` set → move toward it
5. Else ensure `explore_goal` → move toward it

When (1) becomes true while pursuing rabbit, **drop** neutral/explore intent immediately.

**Vore attempt:** before chase step, if adjacent to weakened good/neutral prey and roll succeeds → resolve NPC vore (log + engulf on hit); consumes turn.

Player modal vore unchanged when prey is player.

### Good `pick_intent`

Good NPCs **disregard** neutral NPCs and other good NPCs as intent targets (incidental corridor swap still applies per swap rules).

1. Visible **evil** → chase / attack
2. Else visible **player** → follow (move to minimize distance; stay close)
3. Else `last_known_evil` set → move toward (clear when reached)
4. Else `last_known_player` set → move toward (clear when reached)
5. Else ensure `explore_goal` → move toward it

**Follow player:** treat player position as chase target. If the step would enter the player tile, **do not move** (no-op). Log to **Python console only** (not message log): *"{actor} attempted to swap with the player"* using `entity_log_name(actor)`.

Evil appearing in LOS immediately preempts follow/explore.

### Neutral `pick_intent`

1. If HP > 0 and visible evil → flee
2. Else explore (HP > 0 only for movement; stunned skips)

## NPC swap

In `try_action` when **NPC** is actor and destination has `Fighter`:

```python
def _can_npc_swap(actor, defender) -> bool:
    a, d = alignments
    if Player in defender.tags: return False  # NPC never swaps with player (no-op + console log)
    if a == EVIL and d == EVIL: return True
    if a in (GOOD, NEUTRAL) and d in (GOOD, NEUTRAL): return True
    return False  # cross-alignment → attack if hostile rules apply
```

On NPC swap: swap positions; add defender to `skipped_this_phase` (same as player swap).

Player bump into good/neutral: still player-initiated swap only.

## NPC vore (log only)

**Eligibility:** same rolls as player vore (`should_attempt_vore` generalized for any `Fighter` prey with good/neutral alignment).

**Resolution:**

- Pick narrative type from predator `VoreNarratives` ∩ prefs (same as modal path)
- Miss: log random line from `NPC_VORE_MISS_POOL[type]` — e.g. *"The wolf tries to swallow the knight but fails."*
- Hit: log random line from `NPC_VORE_HIT_POOL[type]` — e.g. *"The wolf swallows the knight whole!"* then `engulf_npc(predator, prey)` — no modal

**Headless engulf:**

- Prey gains `Engulfed`, `Predator` on wolf, co-located position sync
- Prey does not act while engulfed
- No HUD/blind changes for NPC prey
- Defeating predator releases prey (reuse `release_prey_if_defeated_predator`)

**Rescue:** player or good knight bump-attacks holding wolf; at 0 HP wolf defeated → prey released.

Digestion damage / removal deferred.

## Message pools

`src/vore_npc_content.py`:

```python
NPC_VORE_MISS_POOL: dict[str, tuple[str, ...]]  # keys OV, CV, AV
NPC_VORE_HIT_POOL: dict[str, tuple[str, ...]]
```

Templates use `{predator}` and `{prey}` placeholders filled via `entity_log_name`. Filtering via `VoreContentPreferences.is_enabled`.

## Suggested PR plan

| PR | Scope | Manual verify |
|----|--------|----------------|
| 1 | Spawn knights + rabbits; glyphs; examine; static counts | See all three types on map |
| 2 | Good/neutral stunned + messages; evil still defeated; NPC regen | Knight stunned, wakes on regen; wolf regen slower |
| 3 | `AIState`; evil/good/neutral priority; memory; explore | Wolves hunt knights; knights follow you when quiet; rabbits flee |
| 4 | NPC↔NPC swap (alignment rules); skip turn | Two knights pass in corridor |
| 5 | NPC vore logs + headless engulf | Wolf vores stunned knight — log line, no modal |
| 6 | Rescue path polish + tests; supersede E2 spec notes | Knight frees rabbit by defeating wolf |
| 7 | `testing-checklists.md`, acceptance, archive | Full pytest + checklist |

Each PR ships `testing-checklist-prN.md` for in-game verification.

## Test strategy

- `test_spawn_includes_knight_and_rabbit`
- `test_knight_stunned_not_removed`
- `test_evil_still_defeated_at_zero`
- `test_npc_regen_intervals`
- `test_evil_priority_player_over_neutral`
- `test_good_follows_player_when_no_evil`
- `test_good_bump_player_noop_console_only`
- `test_good_ignores_neutral_and_good_targets`
- `test_neutral_flees_only_above_zero_hp`
- `test_explore_goal_reached_picks_new`
- `test_npc_same_alignment_swap`
- `test_npc_never_swaps_onto_player`
- `test_npc_vore_miss_log`
- `test_npc_vore_hit_engulfs_without_modal`
- `test_defeating_predator_frees_npc_prey`

## Supersedes (Enhancements 2)

- Evil **does** pursue neutral as **secondary** goal
- Good/neutral **not defeated** at 0 HP
- NPC↔NPC swap added (player-only swap with good/neutral unchanged)