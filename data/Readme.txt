KD's Vore Roguelike — data folder ability reference
====================================================

This file lists ability tokens that entities.json can use and that the
current game code will load and run. For full field reference on entities,
see SCHEMA.md in this folder. For behavioral rules, see
openspec/specs/npc-abilities/spec.md.


Adding abilities to an entity
-----------------------------

In data/entities.json, set the optional "abilities" field to a JSON array of
strings on any entity definition:

    "abilities": ["Coward"]

    "abilities": ["Smite3", "Knockback"]

    "abilities": ["Summon1 rabbit"]

Rules at load time:
  - Tokens are matched exactly (case-sensitive).
  - Unknown tokens log a one-time warning and are dropped.
  - Duplicate SmiteN tokens collapse to the highest N (e.g. Smite2 + Smite5
    becomes Smite5), with a one-time warning.
  - SummonN <entity_id> requires <entity_id> to exist in entities.json or
    load fails with an error.
  - Multiple non-Smite abilities on one entity stack; see "Stacking" below.

Stock shipped wolf uses an empty list (baseline evil AI with no modifiers):

    "abilities": []


Implemented ability tokens (runtime handlers exist)
---------------------------------------------------

Fixed IDs — use these strings exactly:

  Coward        Flee when below 50% HP if a visible alignment threat exists.
                Good/neutral: flee evil. Evil: flee player/good threats.

  Supercoward   Flee at any HP while alive when a visible threat exists and
                a legal flee step is available.

  Erratic       Three sub-steps per world phase, fixed order:
                (1) optional pursuit move — skipped if already adjacent to
                    an attack target;
                (2) adjacent-only attack (vore/melee);
                (3) mandatory random adjacent move (no-op only if no legal
                    adjacent tile exists).

  Slow          Skip the entire world-phase visit on odd player_turn_count
                (acts on even counts: 0, 2, 4, …).

  Fast          Run the base action plan twice in one world phase (two
                independent intent steps).

  Knockback     On melee or Smite/Path ranged hit with damage > 0, push
                defender one tile along the attack vector when the destination
                is legal. Logs "You are knocked back!" / "{Target} is knocked
                back!" only when the push succeeds and combat is in player FOV.

  Lifedrain     On hit with damage > 0, heal the attacker by damage dealt
                (capped at max_hp). Logs "{Actor} appears healthier." when
                healing applies and combat is in player FOV.


Pattern tokens — syntax matters:

  Smite2 … Smite9
                Enable Smite-targeted attacks at Chebyshev distance 2 through
                N (inclusive), with line of sight. Distance 1 uses melee.
                Ignores entities between shooter and target. Uses
                ranged_accuracy, ranged_min_damage, ranged_max_damage from the
                entity when present; otherwise melee stats. Log verb: smites.
                Examples: "Smite2", "Smite5", "Smite9"
                (Only 2–9 are valid; Smite1 and Smite10+ are not recognized.)

  Range2 … Range9
                Enable Path-targeted attacks at Chebyshev distance 2 through N
                (inclusive), with line of sight. Beam simulation; allies on the
                path cancel the shot. Distance 1 uses melee. Uses ranged_* stats
                when present. Log verb: shoots.
                Examples: "Range2", "Range5", "Range9"

  SummonN <id>  One-shot summon when alignment-appropriate hostiles first
                enter line of sight. Spawns N copies of entity <id> on
                random legal adjacent tiles (partial spawn if space is
                limited). <id> must match an "id" field in entities.json.
                Examples: "Summon1 rabbit", "Summon3 rabbit"
                (N is a positive integer; space required before entity id.)


Stacking (multiple abilities on one entity)
-------------------------------------------

Composition order when building each monster's action plan:

  1. Slow gate     — odd player_turn_count → skip entire visit
  2. Erratic shape — if Erratic: [MOVE, ATTACK, MOVE]; else [MOVE_OR_BUMP]
  3. Fast          — if Fast: repeat the base plan twice

Examples:
  Slow + Fast       — skip on odd turns; on even turns, two MOVE_OR_BUMP steps
  Slow + Erratic    — skip on odd turns; on even turns, full erratic cycle
  Fast + Erratic    — six steps (erratic cycle twice)
  Erratic + SmiteN  — erratic ATTACK step can smite when in range
  Coward + SmiteN   — flee when coward rules apply; otherwise Smite/melee AI

Coward + Supercoward on the same entity: Supercoward behavior wins (flee at
any HP while alive).

Multiple SmiteN tokens: only the highest N is kept.


Activation logs (message log)
-----------------------------

These abilities may add a second FOV-gated line when they fire (in addition
to normal damage lines):

  SummonN         "{Actor} summons aid!"
  SmiteN          smite hit/miss templates (not actor_hits_target)
  Knockback       knockback line only when push succeeds
  Lifedrain       "{Actor} appears healthier." only when HP is restored

No activation log for: Coward, Supercoward, Erratic, Slow, Fast.

Player wand evoke uses Smite targeting; log verb: smite.


Not handled here
----------------

  - Item abilities in weapons.json / armor.json (warn-only; no gameplay)
  - Tokens not listed above (warned and dropped at load)


Quick copy-paste examples for entities.json
-------------------------------------------

    "abilities": []
    "abilities": ["Smite2"]
    "abilities": ["Summon1 rabbit"]
    "abilities": ["Coward"]
    "abilities": ["Supercoward"]
    "abilities": ["Erratic"]
    "abilities": ["Slow"]
    "abilities": ["Fast"]
    "abilities": ["Knockback"]
    "abilities": ["Lifedrain"]
    "abilities": ["Smite3", "Knockback"]
    "abilities": ["Fast", "Erratic"]