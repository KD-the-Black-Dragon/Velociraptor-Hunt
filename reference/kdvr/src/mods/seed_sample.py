"""First-run seed: Sample Mod (disabled) + modding README under user data."""

from __future__ import annotations

from pathlib import Path

from src.mods.paths import ensure_mods_root
from src.mods.state import write_mod_state

SAMPLE_MOD_FOLDER_NAME = "Sample Mod"
MODDING_README_FILENAME = "MODDING_README.txt"

# Valid entities.json for a single placeholder species (disabled by default).
SAMPLE_ENTITIES_JSON = """\
{
  "schema_version": 1,
  "entities": [
    {
      "id": "placeholder_creature",
      "display_name": "creature",
      "glyph": "x",
      "fg": [180, 180, 180],
      "alignment": "evil",
      "mobility": "ground",
      "examine": "This is a generic creature with no special description yet.",
      "proper_name": null,
      "max_hp": 20,
      "evade": 1,
      "ac": 1,
      "accuracy": 1,
      "min_damage": 5,
      "max_damage": 5,
      "ranged_accuracy": 1,
      "ranged_min_damage": 3,
      "ranged_max_damage": 3,
      "experience_points": 30,
      "digestion_damage_per_tick": 3,
      "digest_time": 6,
      "placeholder": true,
      "abilities": [],
      "spawn": {
        "weight": 5,
        "min_depth": 1,
        "max_depth": 1000,
        "terrain": "land",
        "requires_vore_types": []
      },
      "vore_narratives": {
        "OV": [
          {
            "attempt": [
              "{predator} lunges and tries to stuff you into its maw!"
            ],
            "success": [
              "[placeholder] {predator} swallows you whole in one motion.",
              "[placeholder] You slide completely into {predator}'s belly."
            ]
          }
        ],
        "CV": [
          {
            "attempt": [
              "{predator} tries to pull you toward its cock!"
            ],
            "success": [
              "[placeholder] {predator} draws you into its cock.",
              "[placeholder] You are pulled deeper inside {predator}'s ballsack until you're fully contained."
            ]
          }
        ],
        "AV": [
          {
            "attempt": [
              "{predator} turns around, aiming its rear at you!"
            ],
            "success": [
              "[placeholder] {predator} sucks you into its tailhole.",
              "[placeholder] You are pulled fully into {predator}'s backside, which closes behind you."
            ]
          }
        ]
      },
      "digestion_complete": {
        "OV": [
          "[placeholder] {predator} finishes digesting {prey}.",
          "[placeholder] {predator}'s belly settles as {prey} is fully digested."
        ],
        "CV": [
          "[placeholder] {predator} orgasms out what's left of {prey}.",
          "[placeholder] {predator} cums out what's left of {prey}."
        ],
        "AV": [
          "[placeholder] {predator} finishes digesting {prey} in its lower gut.",
          "[placeholder] {predator}'s rear settles as {prey} is fully digested."
        ]
      },
      "npc_vore_hit": {
        "OV": [
          "[placeholder] {predator} swallows {prey} whole!",
          "[placeholder] {predator} gulps {prey} down!"
        ],
        "CV": [
          "[placeholder] {predator} pulls {prey} into its cock!",
          "[placeholder] {predator} draws {prey} into its cock!"
        ],
        "AV": [
          "[placeholder] {predator} sucks {prey} into its rear!",
          "[placeholder] {predator} pulls {prey} into its tailhole!"
        ]
      },
      "npc_vore_miss": {
        "OV": [
          "[placeholder] {predator} tries to swallow {prey}, but fails.",
          "[placeholder] {predator} lunges at {prey} and misses."
        ],
        "CV": [
          "[placeholder] {predator} tries to pull {prey} into its cock, but fails.",
          "[placeholder] {predator} fails to catch {prey} with its cock."
        ],
        "AV": [
          "[placeholder] {predator} tries to pull {prey} into its rear, but fails.",
          "[placeholder] {predator} fails to catch {prey} with its rear."
        ]
      },
      "offscreen_vore": {
        "OV": [
          "[placeholder] From elsewhere, you hear a loud gulp.",
          "[placeholder] From elsewhere, you hear a swallowing sound."
        ],
        "CV": [
          "[placeholder] From elsewhere, you hear a wet slurping sound.",
          "[placeholder] From elsewhere, you hear a strange squelching noise."
        ],
        "AV": [
          "[placeholder] From elsewhere, you hear a squishing sound.",
          "[placeholder] From elsewhere, you hear a muffled squelch."
        ]
      },
      "offscreen_digest": {
        "OV": [
          "[placeholder] From elsewhere, you hear a loud belch.",
          "[placeholder] From elsewhere, you hear a low gurgle."
        ],
        "CV": [
          "[placeholder] From elsewhere, you hear a splattering sound.",
          "[placeholder] From elsewhere, you hear a wet spurt."
        ],
        "AV": [
          "[placeholder] From elsewhere, you hear a low gurgle.",
          "[placeholder] From elsewhere, you hear a soft rumble."
        ]
      },
      "digestion_player_modal": {
        "OV": [
          {
            "phases": [
              "[placeholder] You are digested inside {predator}'s belly.",
              "[placeholder] {predator} appears satisfied as the process finishes."
            ]
          }
        ],
        "CV": [
          {
            "phases": [
              "[placeholder] You are digested inside {predator}'s ballsack.",
              "[placeholder] {predator} appears satisfied as the process finishes."
            ]
          }
        ],
        "AV": [
          {
            "phases": [
              "[placeholder] You are digested inside {predator}'s lower gut.",
              "[placeholder] {predator} appears satisfied as the process finishes."
            ]
          }
        ]
      },
      "engulfed_flavor": {
        "OV": [
          "[placeholder] {predator}'s belly gurgles around you.",
          "[placeholder] Warm slime shifts as {predator} settles."
        ],
        "CV": [
          "[placeholder] {predator}'s sack tightens briefly around you.",
          "[placeholder] A wet pulse rolls through {predator}."
        ],
        "AV": [
          "[placeholder] {predator}'s gut squeezes and releases.",
          "[placeholder] Pressure rolls past you inside {predator}."
        ]
      }
    }
  ]
}
"""

MODDING_README_TEXT = """\
KD's Vore Roguelike — Modding guide
===================================

This folder is your personal mods directory. Your own mod folders are never
overwritten. Game-owned files under mods/ may refresh on launch (see below).

Where mods live
---------------
  mods/
    Sample Mod/          <- example mod (disabled by default; game-owned JSON)
      mod.state            <- one line: E or D, then load order number
      entities.json      <- sample template (refreshed when out of date)
    YourCoolMod/
      mod.state
      entities.json
      weapons.json
      ...

  MODDING_README.txt     <- this file (refreshed on launch when out of date)

Folder name = mod id (shown in Options → Mods...). Spaces are fine.

  This guide file and Sample Mod/entities.json are owned by the game. Edits
  to those paths are overwritten when the shipped text changes. Copy Sample
  Mod to a new folder name before customizing. Put your own notes in a
  separate file if you need them. Sample Mod mod.state (enabled/order) is kept.

Enable / load order
-------------------
  mod.state line format:   E 1     or     D 2
    E = enabled (content loads)
    D = disabled (listed in UI, does not affect play)
    number = load order among mods (lower loads earlier)

  Core install data ALWAYS loads first. Enabled mods then apply in order.

  entities.json: same id deep-merges onto the current definition. Omit a field
  to keep stock (or earlier-mod) values; set a field to overwrite. Nested
  objects (like spawn) merge; arrays replace when present (abilities, fg,
  narrative variant lists, etc.). Brand-new entity ids still need every
  mandatory field.

  Other id catalogs (weapons, armor, potions, wands, throwables, floor_runes,
  macguffins, names): same id fully replaces that entry for the session.

  Prefer Options → Mods... to toggle and reorder. Leaving Mods reloads data.
  Entering Mods with a saved game requires capital Y and DELETES the save
  (mod fingerprint must match to load a run).

Supported content files (same schemas as stock data/)
-----------------------------------------------------
  Entity deep-merge by id:
    entities.json

  Id-merge full replace (entry by entry, later wins):
    weapons.json, armor.json, potions.json, wands.json,
    throwables.json, floor_runes.json, macguffins.json, names.json

  Whole-file replace (if present, replaces entire previous layer):
    dungeon_spawn.json, depth_scaling.json, global_tuning.json,
    depth_jump_start.json, npc_prefixes.json, rescue_gratitude.json,
    ui_layout.json

  Not moddable: Python code, tilesets, fonts.

Key terms
---------
  entity / species
    One creature definition (id like wolf or placeholder_creature).

  alignment
    good  = ally-like AI, no vore
    evil  = hostile, may vore
    neutral = non-hostile by default

  mobility
    ground | fly (or flyer) | aquatic | stationary

  spawn.weight
    Relative chance to appear. 0 = never spawn new copies (id still loads for
    old saves). Higher = more common among eligible depths.

  spawn.min_depth / max_depth
    Inclusive floor range where this species can spawn.

  spawn.requires_vore_types
    Optional capability list: OV / CV / AV. Empty, omitted, or null = no gate.
    Non-empty = (1) spawn when at least one listed type is enabled in the run's
    vore prefs (OR); (2) the species only attempts types in that list ∩ prefs.
    Density target stays the same; other species fill in.
    Unknown tokens are ignored.
    Example: ["CV"] only appears when Cock Vore is enabled, and only attempts CV.
    Example: ["CV", "AV"] appears if CV or AV (or both) is enabled.
    If somehow no enabled type remains attemptable, the engine uses a basic
    internal GENERIC swallow (not an Options toggle).

  max_hp, ac, evade, accuracy, min_damage, max_damage
    Combat stats. evade/accuracy are continuous numbers (not pure %).

  digestion_damage_per_tick
    HP drained per player turn while you are engulfed (evil predators).

  digest_time
    Strikes at 0 HP before digestion completes (evil; default 6 if omitted).

  abilities
    Tokens such as Erratic, Slow, Hands, PreferVore, Range5, Smite5.
    RangeN / SmiteN need sensible ranged_* stats if you want ranged combat.

  placeholder
    true marks unfinished content. Put [placeholder] in prose until rewritten.

  vore narrative types
    OV = oral, CV = cock, AV = anal (player prefs filter which types play).

  {predator} / {prey}
    Placeholders filled at runtime in narrative lines.

Reasonable starting values (rough guide)
----------------------------------------
  Early-depth fodder (depth 1–5)
    max_hp 12–24, damage 2–6, accuracy ~0.8–1.2, evade ~0.5–1.2, ac 0–2
    spawn.weight 3–6, digestion_damage_per_tick 2–3

  Mid-depth (depth 6–12)
    max_hp 30–60, damage 6–12, accuracy ~1.0–1.5, evade ~1.0–1.5, ac 1–4
    spawn.weight 2–4, digestion_damage_per_tick 3–5

  Late-depth (depth 13+)
    max_hp 70–110+, damage 12–22, accuracy ~1.2–1.8, evade ~1.2–2.0, ac 3–8
    spawn.weight 1–3, digestion_damage_per_tick 4–8

  Player starts near max_hp 45 (stock). One vitality rune is +5 max HP.
  Healing potions restore roughly 15 / 38 / 75 depending on tier.

  Glyph: one printable character (not #). fg: [r, g, b] each 0–255.
  Keep min_damage <= max_damage (same for ranged_*).

Sample Mod
----------
  "Sample Mod" ships disabled so it never changes normal play until you enable
  it in Options → Mods.... It adds one gray "x" creature (placeholder_creature)
  so you can see the entities.json shape. Enable it, start a new game, and look
  for glyph x.

  entities.json is game-owned: on launch the game rewrites it when missing or
  different from the shipped template (skips the write when identical). Your
  enabled/order in Sample Mod/mod.state is preserved. Copy the folder to a new
  name before editing if you want a lasting custom mod.

  Full field reference: install's data/SCHEMA.md
  High-level rules: install README (Modding section)

Tips
----
  - Start by copying Sample Mod to a new folder name, then edit.
  - Validate JSON (commas, quotes) before enabling.
  - Bad mod files show an error dialog and are skipped; the game still runs.
  - To change stock species, patch only the fields you mean — e.g. turn off
    wolves with { "id": "wolf", "spawn": { "weight": 0 } } and nothing else.
  - Gate a CV-only monster with
    { "id": "…", "spawn": { "requires_vore_types": ["CV"] } }.
  - Prefer new ids when adding creatures; patch stock ids when altering them.
  - Present keys overwrite (abilities: [] clears abilities). Omit to inherit.
  - spawn.weight: 0 retires a species without breaking old saves that still
    reference the id.
"""


def is_first_run_onboarding(*, tutorial_prompt_answered: bool, vore_prefs_onboarding_complete: bool) -> bool:
    """True when the player still qualifies for new-player orientation."""
    return (not tutorial_prompt_answered) or (not vore_prefs_onboarding_complete)


def seed_first_run_mod_content(
    *,
    mods_root: Path | None = None,
    tutorial_prompt_answered: bool,
    vore_prefs_onboarding_complete: bool,
) -> None:
    """Refresh game-owned mod docs/templates every launch.

    Rewrites ``MODDING_README.txt`` and Sample Mod ``entities.json`` when missing
    or contents differ from the shipped text. Existing Sample Mod ``mod.state``
    (enabled/order) is preserved. Failures are swallowed so a bad user-data
    path cannot block startup.

    ``tutorial_prompt_answered`` / ``vore_prefs_onboarding_complete`` remain in
    the signature for call-site compatibility; Sample Mod is no longer
    first-run-only.
    """
    _ = (tutorial_prompt_answered, vore_prefs_onboarding_complete)
    try:
        root = ensure_mods_root(mods_root)
        refresh_modding_readme(root)
        refresh_sample_mod_entities(root)
    except OSError:
        return


def refresh_modding_readme(mods_root: Path) -> None:
    """Write ``MODDING_README.txt`` if missing or not identical to shipped text."""
    path = mods_root / MODDING_README_FILENAME
    desired = MODDING_README_TEXT
    if path.is_file():
        try:
            if path.read_text(encoding="utf-8") == desired:
                return
        except OSError:
            pass
    path.write_text(desired, encoding="utf-8")


def refresh_sample_mod_entities(mods_root: Path) -> None:
    """Ensure Sample Mod folder + template ``entities.json``; preserve ``mod.state``."""
    mod_dir = mods_root / SAMPLE_MOD_FOLDER_NAME
    mod_dir.mkdir(parents=True, exist_ok=True)
    entities_path = mod_dir / "entities.json"
    desired = SAMPLE_ENTITIES_JSON
    write_entities = True
    if entities_path.is_file():
        try:
            write_entities = entities_path.read_text(encoding="utf-8") != desired
        except OSError:
            write_entities = True
    if write_entities:
        entities_path.write_text(desired, encoding="utf-8")
    state_path = mod_dir / "mod.state"
    if not state_path.is_file():
        # Disabled by default (discovery would otherwise default new folders to E).
        write_mod_state(mod_dir, enabled=False, order=1)
