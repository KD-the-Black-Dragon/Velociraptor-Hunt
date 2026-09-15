# Proposal: 1v1 arena

**Status:** Design approved (2026-07-15) — see `design.md`, `tasks.md`
**Active design:** `openspec/changes/1v1-arena/`  
**Change id:** `1v1-arena`

## Why

To assist with 1v1 balance between the player and a single monster in a straight combat, or to allow players to face (and perhaps be defeated by) a specific monster to see its vore narratives.

## What

1. New command -- from the main menu, the ability to enter a secret keypress combination (ctrl + some key) that prompts the user to enter an entity id into a text box. In this interface with the text box, also provide a list of all known valid entity ids (as gathered from entities.json and any active mods). The list should be *valid* entities only, i.e. Evil alignment. The entity id must match a value from entities.json. If no match, display an error message and allow the user to make a correction. User may press Esc to go back to main menu. It must be an entity of Evil alignment. (Entering a Good or Neutral entity should be rejected.)

2. If a valid entity is entered, a simple 1x10 hallway combat arena is created, with the player on the far left and the entity on the far right. If the enemy entity is Aquatic, it should also have a single water tile. The player is outfitted according to the existing level skip feature. The player's equipment level must be equal to the entity's minimum spawn depth minus 1.

Examples:

If Monster X's minimum spawn depth is 5, then the player shall have the same equipment they would have when starting on depth 4.

If Monster Y's minimum spawn depth is 15, then the player shall have the same equimpent they would have when starting on depth 14.

The same logic already in place for level skipping should be utilized here; the equipment assigned is always dynamic.

3. Although the player may take any actions desired, the general idea is to walk to the right and engage in melee with the enemy entity until the player or monster is victorious.

4. If the player character is digested, follow the normal Game Over flow but do NOT post a Past Run / High Score. There should be a level warp boolean we used in balance-simulator and that can be reused here; that boolean's sole utility is to indicate a Past Run should not be recorded.

5. If the player defeats the enemy entity, display a special modal that says "You have defeated the enemy!". If the user subsequently presses Enter, return to the Main Menu and do NOT post a Past Run / High Score.

6. We also want to create a headless bot, similar to the existing balance-simulator module, that automatically performs 10 battles against every entity. The bot shall simply attempt to move into the enemy entity, or move right (if the entity is not visible) until victory or defeat. This should be easier given that the bot has exactly two priorities: 1. attempt to move into and bump (melee attack) nearest Evil entity, or 2. if no Evil is in sight, move right. (Note: The possibility exists to get engulfed and then regain freedom on the right side of the enemy, so a simple directive of "mash right" will assuredly result in getting stuck against the rightmost wall. And if currently engulfed, moving right is an acceptable move in this case.)

After all 10 rounds, it records the following information in clean CSV format that clearly delineates each entity:
- Enemy id
- Enemy's lowest spawn depth (straight pull from entities.json, as a reminder)
- Victory rate (as a percent, e.g. 50 for 5 wins, 5 losses.)
- Average health remaining (as a percent, e.g. 30 for 30%)
- Average enemy health remaining (As a percent, e.g. 30 for 30%)



## Success

TBD