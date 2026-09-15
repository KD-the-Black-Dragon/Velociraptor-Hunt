"""PR1 apply script: good NPC roster. Run once; leave in tools or soft-remove later."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTITIES_PATH = ROOT / "data" / "entities.json"
NAMES_PATH = ROOT / "data" / "names.json"

CYAN = [120, 220, 255]


def good_entity(
    *,
    entity_id: str,
    display_name: str,
    glyph: str,
    examine: str,
    max_hp: int,
    evade: float,
    ac: int,
    accuracy: float,
    min_damage: int,
    max_damage: int,
    experience_points: int,
    min_depth: int,
    max_depth: int,
    abilities: list[str] | None = None,
    ranged: tuple[float, int, int] | None = None,
    introduction: list[str],
) -> dict:
    body: dict = {
        "id": entity_id,
        "display_name": display_name,
        "glyph": glyph,
        "fg": list(CYAN),
        "alignment": "good",
        "mobility": "ground",
        "examine": examine,
        "proper_name": None,
        "max_hp": max_hp,
        "evade": evade,
        "ac": ac,
        "accuracy": accuracy,
        "min_damage": min_damage,
        "max_damage": max_damage,
        "experience_points": experience_points,
        "abilities": list(abilities or []),
        "spawn": {
            "weight": 1,
            "min_depth": min_depth,
            "max_depth": max_depth,
            "terrain": "land",
        },
        "introduction_log_category": "speech",
        "introduction": introduction,
    }
    if ranged is not None:
        ra, rmin, rmax = ranged
        body["ranged_accuracy"] = ra
        body["ranged_min_damage"] = rmin
        body["ranged_max_damage"] = rmax
    return body


INTRO_SQUIRE = [
    "Squire reporting! I am {name}.",
    "{name}, ready to learn and ready to fight!",
    "I may be new at this, but {name} won't let you down.",
    "Well met! {name} at your service.",
    "{name} here — point me at the nearest beast!",
    "Another friend! I'm {name}.",
    "Courage first, polish later. I am {name}.",
    "{name} stands with you, shield and all.",
    "Don't mind the oversized shield. I'm {name}.",
    "{name} will watch your back — and trip over it only a little.",
    "For the expedition! {name} is here.",
    "I've trained for this. Well… mostly. {name}!",
    "{name}, junior of the order, reporting for duty.",
    "Together we'll clear a path. I am {name}.",
    "Fear not — {name} is eager and mostly competent.",
    "{name} never shies from a righteous scrap.",
    "A pleasure! Call me {name}.",
    "{name} will hold the line… the short one.",
    "Ready when you are. I'm {name}.",
    "{name} has your flank — probably.",
]

INTRO_GUARD = [
    "Guard post open. I am {name}.",
    "{name} on watch. Stay close if you like living.",
    "Perimeter secured — or it will be. {name}.",
    "I am {name}. Eyes sharp, blade sharper.",
    "{name}, ready to keep this hall clean of monsters.",
    "Well met. {name} keeps the watch.",
    "Another soul to guard. I'm {name}.",
    "{name} doesn't nap on duty. Usually.",
    "Quiet steps, loud steel. {name} is with you.",
    "Report: one ferret, one bad attitude toward evil. {name}.",
    "{name} will hold this corridor.",
    "You look like trouble's friend. Perfect. I'm {name}.",
    "{name}, expedition guard — let's move.",
    "I heard a scuffle. Good. I'm {name}.",
    "Stay in my sight line. {name} is here.",
    "{name} patrols so you don't have to.",
    "No surprises on my watch — except me. {name}!",
    "Glad for company. I am {name}.",
    "{name} stands ready.",
    "The watch is yours and mine. {name}.",
]

INTRO_WARRIOR = [
    "Ha! A fight worth having. I am {name}.",
    "{name} joins you — steel first, questions later.",
    "Roar if you need me. I'm {name}.",
    "Well met, ally. {name} is ready.",
    "{name}, warrior of the expedition!",
    "Point me at the largest beast. I am {name}.",
    "Courage suits you. I'm {name}.",
    "{name} does not tip-toe through dungeons.",
    "Another blade for the cause. {name}!",
    "Let them come. I am {name}.",
    "{name} fights beside you with pride.",
    "A fine day for righteous violence. {name}.",
    "I am {name}. Try to keep up!",
    "{name} will carve a path.",
    "Glory and duty. Mostly duty. {name}.",
    "Your flank is loud now. I'm {name}.",
    "{name} never flees a worthy foe.",
    "Stand tall. {name} has arrived.",
    "Together we break them. I am {name}.",
    "{name}, reporting for battle!",
]

INTRO_WARDEN = [
    "Easy now. I am {name}.",
    "{name} will keep the worse currents off you.",
    "Steady steps. I'm {name}, warden of this stretch.",
    "Well met. {name} watches the ways ahead.",
    "{name} here — calm heads, sharp sticks.",
    "I am {name}. Breathe; then fight.",
    "The halls are restless. Good thing I'm {name}.",
    "{name} wards your path.",
    "Another traveler. Stay near. I'm {name}.",
    "Quiet courage is still courage. {name}.",
    "I am {name}. We'll make it through.",
    "{name} prefers planning, accepts brawling.",
    "River-sense in stone halls. Call me {name}.",
    "{name} holds the line without the shouting… much.",
    "Well met, friend. {name}.",
    "I scout, I stand, I strike. {name}.",
    "{name} is with you.",
    "Let the monsters rush. I'm {name}.",
    "A measured blade for a messy place. {name}.",
    "{name}, warden — at your side.",
]

INTRO_BOAR = [
    "{name}. Professional trouble.",
    "I am {name}. Orders help; monsters don't.",
    "{name}, ready to work.",
    "No speeches. I'm {name}. Let's clear rooms.",
    "Well met. {name} hits what needs hitting.",
    "{name} doesn't do fancy. Does done.",
    "Another job, another hallway. I am {name}.",
    "{name} stands with you.",
    "Keep formation if you can. I'm {name}.",
    "I am {name}. Point and stand clear.",
    "{name} has seen worse. Probably.",
    "Boar on duty. Call me {name}.",
    "{name} will hold.",
    "Save the glory for someone else. I'm {name}.",
    "Well met, ally. {name}.",
    "{name} came to finish a fight, not start a tale.",
    "I am {name}. Move when I move.",
    "{name}, at-arms and available.",
    "Quiet kit, loud results. {name}.",
    "{name} is ready.",
]

INTRO_CHAMPION = [
    "I am {name}. The line holds here.",
    "{name} does not yield.",
    "Well met. {name} stands for the expedition.",
    "{name}, champion — your shield if you'll have it.",
    "The deep things will find me first. I am {name}.",
    "{name} has scars enough for both of us.",
    "Courage, friend. {name} is here.",
    "I am {name}. We push forward.",
    "{name} did not climb this far to flinch.",
    "Stand with me. I'm {name}.",
    "{name} meets gryphon-class threats head-on.",
    "Another ally. Good. I am {name}.",
    "{name} keeps the worst off your back.",
    "No retreat worth the name. {name}.",
    "I am {name}. Speak if you need steel.",
    "{name} is ready for the next floor — and the next.",
    "Well met. The work continues. {name}.",
    "{name} will not be the one who breaks.",
    "For those who still climb. I am {name}.",
    "{name}, champion of the company.",
]

INTRO_RAM = [
    "Crossbow ready. I am {name}.",
    "{name} — hold still, target-wise.",
    "Well met. {name} covers the lane.",
    "I am {name}. Distance is a kindness I provide.",
    "{name} doesn't waste bolts. Much.",
    "Another ally in the sights… friendly. I'm {name}.",
    "{name}, reporting with quarrel enough.",
    "I am {name}. Call your marks.",
    "{name} will pin what charges.",
    "Steady. I'm {name}.",
    "Well met. Keep them off my bow arm. {name}.",
    "{name} hits hard up close too — don't test it.",
    "I am {name}. The line behind the line.",
    "{name} is loaded.",
    "Quiet aim, loud finish. {name}.",
    "{name} stands with you — preferably two tiles back.",
    "I am {name}. Ready when you are.",
    "{name}, crossbow of the company.",
    "They can run. I'm {name}.",
    "{name} has your corridor.",
]

INTRO_CLERIC = [
    "Blessings — and bruises for the wicked. I am {name}.",
    "{name} walks with you.",
    "Well met. {name} brings light and a firm crook.",
    "I am {name}. Soft voice, hard Smite.",
    "{name} will keep you standing if I can.",
    "Peace later. Duty now. I'm {name}.",
    "Another soul to shepherd. {name}.",
    "I am {name}. Fear little; fight much.",
    "{name} prays with results.",
    "Well met, friend. {name}.",
    "{name} is here — for the living.",
    "I am {name}. Stay near the light.",
    "{name} heals when possible, smites when necessary.",
    "Courage, and company. I'm {name}.",
    "{name}, cleric of the expedition.",
    "I am {name}. Evil finds no pasture here.",
    "{name} stands between you and the dark.",
    "Gentle until provoked. I'm {name}.",
    "Well met. {name} is ready.",
    "{name} has your spirit — and your flank.",
]


def main() -> None:
    data = json.loads(ENTITIES_PATH.read_text(encoding="utf-8"))
    entities: list[dict] = data["entities"]
    by_id = {e["id"]: e for e in entities}

    knight = by_id["knight"]
    knight["max_hp"] = 36
    knight["evade"] = 2
    knight["ac"] = 4
    knight["accuracy"] = 2.8
    knight["min_damage"] = 9
    knight["max_damage"] = 12
    knight["spawn"] = {
        "weight": 1,
        "min_depth": 5,
        "max_depth": 7,
        "terrain": "land",
    }

    new_entities = [
        good_entity(
            entity_id="dog_squire",
            display_name="dog squire",
            glyph="q",
            examine=(
                "A junior anthro dog of the same order as the dog knights, still growing into "
                "a shield that looks a size too large. Eager, loyal, and slightly breathless "
                "with the thrill of a real expedition."
            ),
            max_hp=16,
            evade=2,
            ac=1,
            accuracy=1.5,
            min_damage=3,
            max_damage=5,
            experience_points=15,
            min_depth=2,
            max_depth=4,
            introduction=INTRO_SQUIRE,
        ),
        good_entity(
            entity_id="ferret_guard",
            display_name="ferret guard",
            glyph="e",
            examine=(
                "A wiry anthro ferret in light mail, whiskers twitching at every distant scrape. "
                "Expedition guards like this one live for clean sight lines, tight corridors, "
                "and the satisfaction of a patrol finished without surprises — or with surprises "
                "properly stabbed."
            ),
            max_hp=34,
            evade=2,
            ac=4,
            accuracy=3.5,
            min_damage=12,
            max_damage=16,
            experience_points=30,
            min_depth=8,
            max_depth=10,
            introduction=INTRO_GUARD,
        ),
        good_entity(
            entity_id="lion_warrior",
            display_name="lion warrior",
            glyph="L",
            examine=(
                "A proud anthro lion in open-faced warrior's kit, mane half-tamed by a travel "
                "band. Loud courage and a ready blade mark the expedition's fighting heart — "
                "the sort who names charges before taking them."
            ),
            max_hp=48,
            evade=2,
            ac=5,
            accuracy=4.2,
            min_damage=14,
            max_damage=18,
            experience_points=35,
            min_depth=11,
            max_depth=13,
            introduction=INTRO_WARRIOR,
        ),
        good_entity(
            entity_id="otter_warden",
            display_name="otter warden",
            glyph="o",
            examine=(
                "A sleek anthro otter with a warder's baton and a traveler's shield, fur still "
                "suggesting rivers even in dry stone. Calm, precise, and quietly stubborn about "
                "keeping allies on the safe side of trouble."
            ),
            max_hp=48,
            evade=2,
            ac=5,
            accuracy=5.0,
            min_damage=15,
            max_damage=20,
            experience_points=40,
            min_depth=14,
            max_depth=16,
            introduction=INTRO_WARDEN,
        ),
        good_entity(
            entity_id="boar_at_arms",
            display_name="boar-at-arms",
            glyph="A",
            examine=(
                "A stocky anthro boar in practical harness and scarred bracers — no knightly "
                "title, only the solid trade of an at-arms. Professional, blunt, and built to "
                "finish hallway fights without ceremony."
            ),
            max_hp=58,
            evade=2,
            ac=6,
            accuracy=5.8,
            min_damage=18,
            max_damage=24,
            experience_points=45,
            min_depth=17,
            max_depth=19,
            introduction=INTRO_BOAR,
        ),
        good_entity(
            entity_id="badger_champion",
            display_name="badger champion",
            glyph="B",
            examine=(
                "A broad anthro badger in scarred plate, stripe and scowl both earned the hard "
                "way. Expedition champion and last wall against gryphon-class threats — grim, "
                "unyielding, and uninterested in a fair fight for the enemy."
            ),
            max_hp=72,
            evade=2,
            ac=6,
            accuracy=6.5,
            min_damage=20,
            max_damage=26,
            experience_points=50,
            min_depth=17,
            max_depth=1000,
            introduction=INTRO_CHAMPION,
        ),
        good_entity(
            entity_id="ram_crossbow",
            display_name="ram crossbow",
            glyph="c",
            examine=(
                "A heavy-set anthro ram with a crossbow as serious as a battering ram and a "
                "melee stance that proves the bolts are not a bluff. Measured, stubborn, and "
                "happiest when the lane is clear and the quarrel is true."
            ),
            max_hp=28,
            evade=2,
            ac=3,
            accuracy=4.0,
            min_damage=7,
            max_damage=10,
            experience_points=32,
            min_depth=6,
            max_depth=8,
            abilities=["Range5"],
            ranged=(4.0, 7, 10),
            introduction=INTRO_RAM,
        ),
        good_entity(
            entity_id="sheep_cleric",
            display_name="sheep cleric",
            glyph="p",
            examine=(
                "A soft-voiced anthro sheep with a polished holy symbol and wool that somehow "
                "stays almost tidy underground. Gentle company until the Smite lands — then "
                "very firm theology."
            ),
            max_hp=32,
            evade=2,
            ac=3,
            accuracy=7.0,
            min_damage=9,
            max_damage=12,
            experience_points=38,
            min_depth=12,
            max_depth=14,
            abilities=["Smite5"],
            ranged=(7.0, 9, 12),
            introduction=INTRO_CLERIC,
        ),
    ]

    # Insert new goods immediately after knight to keep ally defs grouped.
    knight_idx = next(i for i, e in enumerate(entities) if e["id"] == "knight")
    existing_new = {e["id"] for e in new_entities}
    entities = [e for e in entities if e["id"] not in existing_new]
    knight_idx = next(i for i, e in enumerate(entities) if e["id"] == "knight")
    for offset, ent in enumerate(new_entities):
        entities.insert(knight_idx + 1 + offset, ent)
    data["entities"] = entities

    ENTITIES_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    names = {
        "schema_version": 1,
        "names": {
            "knight": json.loads(NAMES_PATH.read_text(encoding="utf-8"))["names"]["knight"],
            "dog_squire": [
                "Squire Bob",
                "Squire Cedric",
                "Squire Tomas",
                "Squire Pip",
                "Squire Harlan",
                "Squire Ned",
                "Squire Quinn",
                "Squire Miles",
                "Squire Rowan",
                "Squire Felix",
                "Squire Ollie",
                "Squire Jasper",
                "Squire Theo",
                "Squire Sam",
                "Squire Benny",
                "Squire Cole",
                "Squire Duncan",
                "Squire Emmet",
                "Squire Finn",
                "Squire Gus",
                "Squire Howie",
                "Squire Ian",
                "Squire Jules",
                "Squire Kit",
                "Squire Lem",
                "Squire Nat",
                "Squire Owen",
                "Squire Paul",
                "Squire Remy",
                "Squire Scout",
            ],
            "ferret_guard": [
                "Guard Helga",
                "Guard Brisk",
                "Guard Vesper",
                "Guard Nib",
                "Guard Sable",
                "Guard Tine",
                "Guard Wren",
                "Guard Pike",
                "Guard Lur",
                "Guard Moss",
                "Guard Reed",
                "Guard Flint",
                "Guard Harrow",
                "Guard Jit",
                "Guard Kest",
                "Guard Lark",
                "Guard Mir",
                "Guard Nox",
                "Guard Orin",
                "Guard Pratt",
                "Guard Quill",
                "Guard Rill",
                "Guard Softstep",
                "Guard Tallow",
                "Guard Umber",
                "Guard Varn",
                "Guard Wisp",
                "Guard Yarrow",
                "Guard Zell",
                "Guard Clip",
            ],
            "lion_warrior": [
                "Warrior Leo",
                "Warrior Roran",
                "Warrior Sablemane",
                "Warrior Kest",
                "Warrior Drae",
                "Warrior Halla",
                "Warrior Tor",
                "Warrior Vex",
                "Warrior Bram",
                "Warrior Calla",
                "Warrior Dorn",
                "Warrior Eira",
                "Warrior Flintmane",
                "Warrior Gorr",
                "Warrior Hadi",
                "Warrior Ivar",
                "Warrior Jora",
                "Warrior Kael",
                "Warrior Lune",
                "Warrior Mav",
                "Warrior Nuri",
                "Warrior Orsa",
                "Warrior Pyre",
                "Warrior Rusk",
                "Warrior Soren",
                "Warrior Tali",
                "Warrior Ulric",
                "Warrior Vara",
                "Warrior Wulf",
                "Warrior Zane",
            ],
            "otter_warden": [
                "Warden Ness",
                "Warden Brook",
                "Warden Reed",
                "Warden Kelp",
                "Warden Mira",
                "Warden Drift",
                "Warden Silt",
                "Warden Cove",
                "Warden Pebble",
                "Warden Rill",
                "Warden Torrent",
                "Warden Eddy",
                "Warden Foam",
                "Warden Glen",
                "Warden Haven",
                "Warden Inlet",
                "Warden Jetty",
                "Warden Kedge",
                "Warden Lagoon",
                "Warden Marsh",
                "Warden Nettle",
                "Warden Oxbow",
                "Warden Pool",
                "Warden Quay",
                "Warden Rapids",
                "Warden Shoal",
                "Warden Tide",
                "Warden Undertow",
                "Warden Vale",
                "Warden Weft",
            ],
            "boar_at_arms": [
                "Garrick-at-arms",
                "Bram-at-arms",
                "Hilda-at-arms",
                "Tusk-at-arms",
                "Oren-at-arms",
                "Marta-at-arms",
                "Colt-at-arms",
                "Rusk-at-arms",
                "Dorn-at-arms",
                "Piet-at-arms",
                "Sable-at-arms",
                "Tor-at-arms",
                "Venn-at-arms",
                "Willa-at-arms",
                "Yorick-at-arms",
                "Boarheart-at-arms",
                "Kell-at-arms",
                "Lute-at-arms",
                "Nash-at-arms",
                "Peck-at-arms",
                "Quinn-at-arms",
                "Roth-at-arms",
                "Sten-at-arms",
                "Ulma-at-arms",
                "Varr-at-arms",
                "Weld-at-arms",
                "Xan-at-arms",
                "Yeva-at-arms",
                "Zeb-at-arms",
                "Holt-at-arms",
            ],
            "badger_champion": [
                "Champion Brock",
                "Champion Grim",
                "Champion Hilda",
                "Champion Stripe",
                "Champion Dorn",
                "Champion Marta",
                "Champion Tor",
                "Champion Veld",
                "Champion Ash",
                "Champion Bor",
                "Champion Cinder",
                "Champion Dusk",
                "Champion Flint",
                "Champion Granite",
                "Champion Helm",
                "Champion Iron",
                "Champion Jora",
                "Champion Kest",
                "Champion Lode",
                "Champion Mound",
                "Champion Norr",
                "Champion Oak",
                "Champion Pike",
                "Champion Quarry",
                "Champion Ridge",
                "Champion Stone",
                "Champion Thane",
                "Champion Underhill",
                "Champion Varn",
                "Champion Wardenstripe",
            ],
            "ram_crossbow": [
                "Crossbow Bram",
                "Crossbow Horn",
                "Crossbow Serta",
                "Crossbow Quill",
                "Crossbow Bolt",
                "Crossbow Ramm",
                "Crossbow Tilda",
                "Crossbow Varn",
                "Crossbow Wether",
                "Crossbow Apex",
                "Crossbow Buck",
                "Crossbow Cliff",
                "Crossbow Drift",
                "Crossbow Ewe",
                "Crossbow Flint",
                "Crossbow Gruff",
                "Crossbow Heft",
                "Crossbow Ivy",
                "Crossbow Jolt",
                "Crossbow Knurl",
                "Crossbow Ledge",
                "Crossbow Moss",
                "Crossbow Nock",
                "Crossbow Orin",
                "Crossbow Peak",
                "Crossbow Quarrel",
                "Crossbow Ridge",
                "Crossbow Stock",
                "Crossbow Thrum",
                "Crossbow Umber",
            ],
            "sheep_cleric": [
                "Cleric Agnes",
                "Cleric Bell",
                "Cleric Clover",
                "Cleric Dove",
                "Cleric Ellen",
                "Cleric Faith",
                "Cleric Grace",
                "Cleric Hazel",
                "Cleric Iris",
                "Cleric June",
                "Cleric Mercy",
                "Cleric Nell",
                "Cleric Olive",
                "Cleric Peace",
                "Cleric Quinn",
                "Cleric Ruth",
                "Cleric Softwool",
                "Cleric Tallow",
                "Cleric Unity",
                "Cleric Vera",
                "Cleric Wisp",
                "Cleric Yarn",
                "Cleric Abel",
                "Cleric Benedict",
                "Cleric Clement",
                "Cleric Dunstan",
                "Cleric Elias",
                "Cleric Florian",
                "Cleric Giles",
                "Cleric Hearth",
            ],
        },
    }
    NAMES_PATH.write_text(
        json.dumps(names, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("Updated", ENTITIES_PATH)
    print("Updated", NAMES_PATH)
    print("entity count", len(entities))
    goods = [e["id"] for e in entities if e.get("alignment") == "good"]
    print("goods", goods)


if __name__ == "__main__":
    main()
