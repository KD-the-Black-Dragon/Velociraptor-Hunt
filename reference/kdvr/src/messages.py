from __future__ import annotations

import random

"""
User-facing message strings.

Terminology policy: use defeated / stunned / digested — never kill, die, or death.
"""


def welcome() -> str:
    return "Welcome to KD's Vore Roguelike."


def game_saved() -> str:
    return "Game saved."


def save_failed() -> str:
    return "Save failed."


def unknown_difficulty_using_fallback(
    raw_difficulty: str,
    fallback_display_name: str,
) -> str:
    return (
        f"Unknown difficulty '{raw_difficulty}'; using {fallback_display_name}."
    )


def save_sanitize_detail_items(shown: str) -> str:
    return f"removed unknown items ({shown})"


def save_sanitize_detail_creatures(shown: str) -> str:
    return f"removed unknown creatures ({shown})"


def save_sanitize_detail_prefixes(shown: str) -> str:
    return f"cleared unknown prefixes ({shown})"


def save_sanitize_detail_fallback() -> str:
    return "removed outdated content"


def save_sanitize_dropped(detail: str) -> str:
    return (
        "Some data from this save is no longer in the game and was dropped "
        f"so you can keep playing ({detail})."
    )


def dungeon_regenerated() -> str:
    return "A new dungeon awaits."


def come_here_shout() -> str:
    return 'You shout, "Come here!"'


def come_here_hoarse() -> str:
    return "You'll go hoarse if you shout too much."


def come_here_engulfed_fizzle() -> str:
    return "You shout, but you're not sure anyone heard you."


def dismiss_exits_dungeon(name: str) -> str:
    return f"{name} exits the dungeon."


def dismiss_invalid_target() -> str:
    return "Invalid target. (Allied NPCs only)"


def stunned_cleared_debug() -> str:
    return "You recover from being stunned."


def player_stunned() -> str:
    return "You are stunned."


def _hit_verb(actor: str) -> str:
    return "hit" if actor == "You" else "hits"


def _miss_verb(actor: str) -> str:
    return "miss" if actor == "You" else "misses"


def actor_hits_target(actor: str, target: str, damage: int) -> str:
    return f"{actor} {_hit_verb(actor)} {target} for {damage} damage."


def actor_misses_target(actor: str, target: str) -> str:
    return f"{actor} {_miss_verb(actor)} {target}."


def actor_hits_target_no_damage(actor: str, target: str) -> str:
    if actor == "You":
        return f"You hit {target} but deal no damage."
    return f"{actor} hits {target} but deals no damage."


def npc_smites_target(actor: str, target: str, damage: int) -> str:
    return f"{actor} smites {target} for {damage} damage."


def npc_smites_target_no_damage(actor: str, target: str) -> str:
    return f"{actor} smites {target} but deals no damage."


def npc_smites_at_target_miss(actor: str, target: str) -> str:
    return f"{actor} smites {target} but misses."


def npc_shoots_target(actor: str, target: str, damage: int) -> str:
    return f"{actor} shoots {target} for {damage} damage."


def npc_shoots_target_no_damage(actor: str, target: str) -> str:
    return f"{actor} shoots {target} but deals no damage."


def npc_shoots_at_target_miss(actor: str, target: str) -> str:
    return f"{actor} shoots at {target} but misses."


def player_smites_target(target: str, damage: int) -> str:
    return f"You smite {target} for {damage} damage."


def player_smites_target_no_damage(target: str) -> str:
    return f"You smite {target} but deal no damage."


def player_smites_at_target_miss(target: str) -> str:
    return f"You smite {target} but miss."


def npc_summons_aid(actor: str) -> str:
    return f"{actor} summons aid!"


def player_knocked_back() -> str:
    return "You are knocked back!"


def target_knocked_back(target: str) -> str:
    return f"{target} is knocked back!"


def npc_appears_healthier(actor: str) -> str:
    return f"{actor} appears healthier."


def target_defeated(target: str) -> str:
    return f"{target} was defeated."


def player_swap_places(name: str) -> str:
    return f"You swap places with {name}."


def inventory_full() -> str:
    return "Your inventory is full."


def item_pickup(display_name: str, slot: str) -> str:
    return f"You pick up {display_name} into slot '{slot}'."


def item_pickup_stacked(count: int, display_name: str, slot: str) -> str:
    return f"You pick up {display_name} into slot '{slot}' ({count} total)."


def nothing_here_to_pickup() -> str:
    return "There is nothing here to pick up."


def inventory_empty() -> str:
    return "Your inventory is empty."


def nothing_to_drop() -> str:
    return "You have nothing to drop."


def item_dropped(display_name: str) -> str:
    return f"You drop {display_name}."


def no_weapons() -> str:
    return "You have no weapons."


def no_armor() -> str:
    return "You have no armor."


def wield_item(display_name: str) -> str:
    return f"You wield {display_name}."


def wear_item(display_name: str) -> str:
    return f"You wear {display_name}."


def already_wielding() -> str:
    return "You're already wielding that."


def already_wearing() -> str:
    return "You're already wearing that."


def item_destroyed(display_name: str) -> str:
    return f"Your {display_name} falls apart."


def slot_empty(slot: str) -> str:
    return f"Slot '{slot}' is empty."


def no_potions() -> str:
    return "You have no potions."


def cant_drink_that() -> str:
    return "You can't drink that."


def no_wands() -> str:
    return "You have no wands."


def cant_evoke_that() -> str:
    return "You can't evoke that."


def wand_breaks(display_name: str) -> str:
    return f"Your {display_name} breaks!"


def not_the_best_target() -> str:
    return "Not the best target."


def no_valid_targets_in_range() -> str:
    return "No valid targets in range."


def nothing_to_throw() -> str:
    return "You have nothing to throw."


def throw_at_which_target(display_name: str) -> str:
    return f"Throw {display_name} at which target?"


def throw_path_blocked() -> str:
    return "Something is in the way."


def throw_no_target_there() -> str:
    return "There's no target there."


def player_throw_misses_target(target: str) -> str:
    return f"Your throw misses the {target}."


def throwable_stack_empty(display_name: str) -> str:
    return f"Your last {display_name} is gone."


def potion_heal(display_name: str, amount: int) -> str:
    return f"You drink {display_name} and recover {amount} HP."


def potion_no_effect(display_name: str) -> str:
    return f"You drink {display_name} but are already at full health."


def potion_magic_mapping(display_name: str) -> str:
    return f"You drink {display_name}. The dungeon's layout becomes clear in your mind."


def potion_haste(display_name: str) -> str:
    return f"You drink {display_name}. Time seems to accelerate around you."


def potion_might(display_name: str) -> str:
    return f"You drink {display_name}. Battle prowess floods your limbs."


def potion_antacid(display_name: str) -> str:
    return f"You drink {display_name}. Your skin becomes more resilient."


def effect_haste_wore_off() -> str:
    return "You slow back to normal speed."


def effect_might_wore_off() -> str:
    return "Your heightened battle prowess fades."


def effect_antacid_wore_off() -> str:
    return "Your skin loses its magical resilience."


def potion_teleport_delay(display_name: str) -> str:
    return f"You drink {display_name}. You feel unstable."


def teleport_success() -> str:
    return "Your surroundings blur — you reappear elsewhere!"


def teleport_escape() -> str:
    return "Space wrenches you free — you reappear elsewhere!"


def teleport_failed() -> str:
    return "Space twists, but there is nowhere to go."


def blink_where() -> str:
    return "Blink where? (Enter confirm, Esc cancel)"


def blink_success(display_name: str) -> str:
    return f"You drink {display_name} and reappear nearby!"


def blink_invalid_out_of_sight() -> str:
    return "Invalid - cannot blink outside of sight radius."


def blink_invalid_not_walkable() -> str:
    return "Invalid - tile is not walkable."


def blink_invalid_occupied() -> str:
    return "Invalid - that tile is occupied."


def potion_summon_success(display_name: str, ally_name: str) -> str:
    return f"You drink {display_name}. {ally_name} appears at your side!"


def potion_summon_failed(display_name: str) -> str:
    return f"You drink {display_name}, but no ally can appear here."


def item_unknown() -> str:
    return "You don't know how to use that item."


def stunned_too_tired_to_move() -> str:
    return "You're too tired to move."


def no_longer_stunned() -> str:
    return "You are no longer stunned."


def player_being_digested() -> str:
    return "You are being digested!!"


def npc_stunned(name: str) -> str:
    return f"{name} is stunned!"


def npc_no_longer_stunned(name: str) -> str:
    return f"{name} is no longer stunned."


def npc_appears_dazed(name: str) -> str:
    return f"{name} appears dazed."


def npc_no_longer_dazed(name: str) -> str:
    return f"{name} is no longer dazed."


def good_attempted_player_swap(actor: str) -> str:
    return f"{actor} attempted to swap with the player"


def evil_frustrated_by_blocker(actor: str, blocker: str, desired: str) -> str:
    return (
        f"{actor} snarls at {blocker} - {blocker} is blocking the way to {desired}!"
    )


def vore_attempt_evaded(possessive: str) -> str:
    return f"You evaded {possessive} vore attempt."


def vore_attempt_succeeded_temp(possessive: str) -> str:
    """Temporary PR 2 log until PR 3 modal narrative replaces it."""
    return f"{possessive} vore attempt succeeds!"


def vore_escaped(name: str) -> str:
    return f"You escape from {name}."


def npc_freed_from_predator(prey: str, predator: str) -> str:
    return f"{prey} is freed from {predator}."


def engulfed_pack_blocked() -> str:
    return "You cannot reach your pack while engulfed."


def cant_enter_deep_water() -> str:
    return "You can't enter deep water."


def going_deeper_wont_help() -> str:
    return "Going deeper won't help you here!"


def no_stairs_here() -> str:
    return "There are no stairs here."


def examine_engulfed_cant_see() -> str:
    return "You can't see anything!"


def examine_nothing_here() -> str:
    return "There is nothing of interest here."


def examine_items_on_floor_header() -> str:
    return "Items on the floor:"


_STRUGGLE_MESSAGES: tuple[str, ...] = (
    "You struggle to break free.",
    "You fight to break free.",
)


def pick_struggle_message(rng: random.Random) -> str:
    return rng.choice(_STRUGGLE_MESSAGES)


def debug_all_monsters_weakened() -> str:
    return "Debug: all monsters weakened."


def debug_omniscient_vision_enabled() -> str:
    return "Debug: omniscient map vision enabled (F5 toggles; NPC sight unchanged)."


def debug_omniscient_vision_disabled() -> str:
    return "Debug: omniscient map vision disabled (F5 toggles)."


def water_testing_mode_enabled() -> str:
    return "Water-heavy map generation enabled (F3 toggles; R regens)."


def water_testing_mode_disabled() -> str:
    return "Water-heavy map generation disabled (F3 toggles; R regens)."


def layout_archetype_force_boxy() -> str:
    return "Layout archetype forced: boxy (F4 cycles; R regens)."


def layout_archetype_force_organic() -> str:
    return "Layout archetype forced: organic (F4 cycles; R regens)."


def layout_archetype_force_hybrid() -> str:
    return "Layout archetype forced: hybrid (F4 cycles; R regens)."


def layout_archetype_force_cleared() -> str:
    return "Layout archetype force cleared — 40/40/20 mix (F4 cycles; R regens)."


def close_door_choose_direction() -> str:
    return "Close door — choose a direction."


def door_opened() -> str:
    return "You open the door."


def npc_opens_door(actor: str) -> str:
    return f"{actor} opens the door."


def something_opens_door() -> str:
    return "Something opens the door."


def npc_breaks_down_door(actor: str) -> str:
    return f"{actor} breaks down the door!"


def something_breaks_down_door() -> str:
    return "Something breaks down the door!"


def door_closed() -> str:
    return "You close the door."


def no_open_door_there() -> str:
    return "There's no open door there."


def something_in_the_way() -> str:
    return "There's something in the way."


def rune_activated(display_name: str, bonus: str) -> str:
    return f"You absorb the {display_name} ({bonus})."


def rest_start() -> str:
    return "You start resting."


def rest_engulfed_no_time() -> str:
    return "This is no time to rest!"


def rest_already_full_health() -> str:
    return "You are already at full health."


def rest_too_dangerous_now() -> str:
    return "It's too dangerous to rest now!"


def rest_finish() -> str:
    return "You finish resting."


def rest_fully_healed() -> str:
    return "You are fully healed."


def rest_danger_approaches() -> str:
    return "Danger approaches!"


def rest_interrupted_by_attack() -> str:
    return "It's hard to rest while under attack!"


def good_ally_shouts_alarm(name: str) -> str:
    return f"{name} shouts in alarm!"


def autoexplore_start() -> str:
    return "You begin exploring."


def autoexplore_complete() -> str:
    return "Exploration complete."


def autoexplore_engulfed() -> str:
    return "You're already exploring something's digestive tract."


def autoexplore_enemy_in_sight() -> str:
    return "There's an enemy in sight!"


def autoexplore_too_injured() -> str:
    return "You are too injured to autoexplore."


def attack_empty_air() -> str:
    return "You attack the empty air."