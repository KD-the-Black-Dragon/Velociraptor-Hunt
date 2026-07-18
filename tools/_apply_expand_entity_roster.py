"""One-shot: apply expand-entity-roster stock content to data/entities.json."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTITIES = ROOT / "data" / "entities.json"


def stub_block(name: str) -> dict:
    """Minimal complete evil narrative block (placeholder quality)."""
    return {
        "vore_narratives": {
            "OV": [
                {
                    "attempt": [f"[placeholder] The {name} lunges maw-first!"],
                    "success": [
                        f"[placeholder] The {name} forces you into its hot gut.",
                        f"[placeholder] You settle fully inside the {name}, sealed tight.",
                    ],
                }
            ],
            "CV": [
                {
                    "attempt": [f"[placeholder] The {name} presents itself cock-first!"],
                    "success": [
                        f"[placeholder] The {name} pulls you into its shaft.",
                        f"[placeholder] You are packed into the {name}'s swollen sack.",
                    ],
                }
            ],
            "AV": [
                {
                    "attempt": [f"[placeholder] The {name} turns rump-first!"],
                    "success": [
                        f"[placeholder] The {name} draws you up its rear.",
                        f"[placeholder] You are sealed in the {name}'s lower gut.",
                    ],
                }
            ],
        },
        "digestion_complete": {
            "OV": [f"[placeholder] {{predator}} gurgles {{prey}} into {name}-fat."],
            "CV": [f"[placeholder] {{predator}} empties {{prey}} from its cock."],
            "AV": [f"[placeholder] {{predator}} works {{prey}} into its haunches."],
        },
        "npc_vore_hit": {
            "OV": [f"[placeholder] {{predator}} swallows {{prey}} whole!"],
            "CV": [f"[placeholder] {{predator}} sucks {{prey}} into its cock!"],
            "AV": [f"[placeholder] {{predator}} draws {{prey}} into its rear!"],
        },
        "npc_vore_miss": {
            "OV": [f"[placeholder] {{predator}} snaps at {{prey}} and misses."],
            "CV": [f"[placeholder] {{predator}} fails to grab {{prey}}."],
            "AV": [f"[placeholder] {{predator}} backs into empty air."],
        },
        "offscreen_vore": {
            "OV": ["[placeholder] A wet gulp echoes from elsewhere."],
            "CV": ["[placeholder] A lewd suck echoes from elsewhere."],
            "AV": ["[placeholder] A muffled squelch echoes from elsewhere."],
        },
        "offscreen_digest": {
            "OV": ["[placeholder] A distant gurgle settles into silence."],
            "CV": ["[placeholder] A distant pulse and hiss fade away."],
            "AV": ["[placeholder] A distant rolling gurgle fades."],
        },
        "digestion_player_modal": {
            "OV": [
                {
                    "phases": [
                        f"[placeholder] The {name}'s insides work on you until nothing remains but a full belly.",
                        f"[placeholder] Digestion finishes. You are {name}-fat.",
                    ]
                }
            ],
            "CV": [
                {
                    "phases": [
                        f"[placeholder] The {name}'s insides work on you until nothing remains but a full belly.",
                        f"[placeholder] The {name} empties what is left of you.",
                    ]
                }
            ],
            "AV": [
                {
                    "phases": [
                        f"[placeholder] The {name}'s insides work on you until nothing remains but a full belly.",
                        f"[placeholder] The {name}'s lower gut finishes its work.",
                    ]
                }
            ],
        },
    }


def base_combat(**kw: object) -> dict:
    defaults = {
        "proper_name": None,
        "placeholder": True,
        "ranged_accuracy": 0,
        "ranged_min_damage": 0,
        "ranged_max_damage": 0,
        "abilities": [],
        "spawn_requires_water": False,
    }
    defaults.update(kw)
    return defaults


# --- Quality rewrites ---

CAVE_RAT = {
    **base_combat(
        id="cave_rat",
        display_name="cave rat",
        glyph="c",
        fg=[150, 120, 70],
        alignment="evil",
        mobility="ground",
        examine=(
            "An oversized dungeon rat, nearly the bulk of a small dog, with oily brown fur "
            "that clings in slick mats to its flanks. Yellow teeth jut from a constantly "
            "working jaw, and thick ropes of sticky slobber string from its lips with every "
            "breath. Its long, naked tail coils and uncoils with unpleasant purpose, as if "
            "it means to catch something."
        ),
        max_hp=7,
        evade=1,
        ac=0,
        accuracy=0.48,
        min_damage=2,
        max_damage=3,
        experience_points=35,
        digestion_damage_per_tick=2,
        digest_time=6,
        abilities=["Erratic"],
        spawn={"weight": 3, "min_depth": 1, "max_depth": 6, "terrain": "land"},
    ),
    "vore_narratives": {
        "OV": [
            {
                "attempt": [
                    "The cave rat lunges, yellow teeth bared, a thick rope of sticky slobber whipping from its jaws!"
                ],
                "success": [
                    "Those yellow teeth clamp the air beside your ear as the rat's maw stretches over your head, flooding your face with hot, oily spit that mats your hair to your scalp.",
                    "Its naked tail lashes around your waist like a wet cable and hauls you forward while the rat's throat works in hard, greasy swallows, cramming your shoulders into a tunnel lined with slick, clinging slime.",
                    "The oily fur of its belly rasps past your back as you fold into a crushing, narrow gut that squeezes from every side, the walls so tight you can barely draw breath, every inch painted in the same hot, slick film.",
                    "The last of you vanishes past the yellow teeth. The rat sits heavily, belly a taut, greasy oval, tail still twitching as if proud of the catch it made."
                ],
            }
        ],
        "CV": [
            {
                "attempt": [
                    "The cave rat rears and swings its hips forward, a slick, oily length twitching toward you while its tail snags for purchase!"
                ],
                "success": [
                    "The tip flares and drags over your face in one sticky pull, flooding your senses with heat and oil as the rat's tail cinches your arms tight against your sides.",
                    "Each thrashing yank of that tail works another few inches of you into the greasy shaft; the tunnel clings and slides, never quite dry, never quite loose enough to fight.",
                    "Your hips and legs follow in a series of wet, straining gulps until you are packed into a swollen, oily sack that wraps you like a second skin, walls pressed flush to every limb.",
                    "Your feet slip through with a final sticky pop. The rat's sack hangs heavy and tight; it chitters once, already grinding its hips as if the work of packing you away were half the reward."
                ],
            }
        ],
        "AV": [
            {
                "attempt": [
                    "The cave rat whirls and flings its rump back, tail looping toward your wrist like a snare!"
                ],
                "success": [
                    "The tail cinches your forearm and yanks you face-first into a puckered ring that stretches with an oily sheen, sealing over your head in one greedy clench.",
                    "You are hauled in by the tail and the rat's own grinding shoves, the lower gut a hot, slimy sleeve that grips so tight your shoulders have to corkscrew to fit.",
                    "Every thrash packs you deeper into that narrow, grease-slick chamber until your feet clear the rim and the ring snaps shut, leaving you folded in a crushing coil of oily flesh.",
                    "The rat settles, haunches bulging obscenely, tail still wrapped once around the swollen mass as if to keep its prize from shifting."
                ],
            }
        ],
    },
    "digestion_complete": {
        "OV": [
            "{predator} chitters as its greasy belly rounds, then shrinks — {prey} worked into oily rat-fat.",
            "A long, wet gurgle and {predator}'s taut gut slumps smooth; {prey} is gone."
        ],
        "CV": [
            "{predator} shudders and empties a thick, sticky flood where {prey} used to be.",
            "{predator}'s swollen sack clenches and drains, leaving only a slick stain and a thinner rat."
        ],
        "AV": [
            "{predator}'s haunches clench and gurgle; the {prey}-bulge melts into greasy rump-fat.",
            "A rolling squelch and {predator}'s lower gut settles — {prey} is rat-plush now."
        ],
    },
    "npc_vore_hit": {
        "OV": [
            "{predator} wraps its tail and gulps {prey} down in a string of oily swallows!",
            "{predator}'s yellow teeth flash; a moment later {prey} is a greasy bulge in its belly!"
        ],
        "CV": [
            "{predator} snags {prey} with its tail and hauls them into its slick shaft!",
            "{predator} packs {prey} into a tight, oily sack with frantic little thrusts!"
        ],
        "AV": [
            "{predator} lashes its tail around {prey} and draws them up its rear!",
            "{predator} backs onto {prey} and seals them into a crushing, greasy lower gut!"
        ],
    },
    "npc_vore_miss": {
        "OV": [
            "{predator} snaps yellow teeth at {prey} and only flings slobber.",
            "{predator} lunges for {prey}, but its tail finds empty air."
        ],
        "CV": [
            "{predator} tries to snag {prey} for a better angle and loses the grip.",
            "{predator} rears cock-first at {prey}, but {prey} twists free of the tail."
        ],
        "AV": [
            "{predator} whips its tail at {prey} and misses, skidding on oily paws.",
            "{predator} backs toward {prey} and only brushes them with its rump."
        ],
    },
    "offscreen_vore": {
        "OV": [
            "You hear a wet, struggling gulp and a short, vicious chitter.",
            "You hear a tail lash the stone, then a series of greasy swallows."
        ],
        "CV": [
            "You hear a sticky, elongated pull and frantic chittering.",
            "You hear something cinch and a muffled, oily suck nearby."
        ],
        "AV": [
            "You hear a tail whip and a thick, sealing squelch.",
            "You hear a short struggle, then a greasy packing sound."
        ],
    },
    "offscreen_digest": {
        "OV": ["You hear a long, wet gurgle and a satisfied chitter."],
        "CV": ["You hear a sticky splat and fading little shudders."],
        "AV": ["You hear a rolling squelch that settles into silence."],
    },
    "digestion_player_modal": {
        "OV": [
            {
                "phases": [
                    "The cave rat's gut is a crushing sleeve of heat and oil, walls pressed so flush to your body that every breath steals space you do not have. Sticky slime works into the seams of your clothes and skin while the rat's heartbeat thumps through the taut hide above you.",
                    "The walls knead harder, the oil film thickening until your edges soften and run. You sink into the clinging dark by inches, folded tighter, until the bulge you made rounds smooth and the rat's belly shrinks back to a heavy, greasy oval of fresh fat."
                ]
            }
        ],
        "CV": [
            {
                "phases": [
                    "Packed in the rat's swollen sack, you are wrapped in a second skin of hot, oily flesh that never loosens. Every twitch of the rat's hips grinds the walls tighter, smearing you in slick heat until you can no longer tell where you end and the slime begins.",
                    "The sack clenches in long, sticky waves. You soften, run, and thin into the churning dark until a final shudder empties what is left of you onto the stone in a thick flood, and the sack collapses to almost nothing."
                ]
            }
        ],
        "AV": [
            {
                "phases": [
                    "Wedged in the rat's lower gut, you are coiled in a narrow, greasy trap that refuses to yield a finger's width. The oily walls slide and clamp in time with the rat's restless tail, working slime into every fold of you.",
                    "The chamber milks and crushes until you melt into its lining. The haunches above you settle heavier and smoother as you become nothing but a bit of greasy plush on a well-fed cave rat."
                ]
            }
        ],
    },
}


SLIME = {
    **base_combat(
        id="slime",
        display_name="slime",
        glyph="j",
        fg=[80, 200, 120],
        alignment="evil",
        mobility="ground",
        examine=(
            "A silent mass of translucent gel, roughly the size of a crouched person, "
            "resting on the stone without a face, a mouth, or any organ you can name. "
            "Light bends wrong inside it. When it moves, it does not crawl so much as "
            "reconsider where its edges belong."
        ),
        max_hp=14,
        evade=0,
        ac=1,
        accuracy=0.5,
        min_damage=1,
        max_damage=2,
        experience_points=40,
        digestion_damage_per_tick=2,
        digest_time=7,
        abilities=[],
        spawn={"weight": 2, "min_depth": 1, "max_depth": 7, "terrain": "land"},
    ),
    "vore_narratives": {
        "OV": [
            {
                "attempt": [
                    "The slime surges forward without a sound, a wave of clear gel rising to take your shape."
                ],
                "success": [
                    "Cool gel climbs your boots and calves in a single smooth sheet, sealing over fabric and skin with a soft, airtight cling that leaves no gap for air or argument.",
                    "The mass climbs higher, folding over your hips and chest; inside the translucent bulk you see your own limbs dimly, held in place by a pressure that is firm without being cruel — only absolute.",
                    "Your head slips under last. Sound dies. The dungeon becomes a blurred smear through living glass while the slime's body contracts around you into a neat, upright oval.",
                    "The gel settles. Bubbles drift past your face and vanish. Outside, the slime is once again a quiet mound — thicker now, with your outline faintly suggested and then smoothed away."
                ],
            }
        ],
        "CV": [
            {
                "attempt": [
                    "A thick column of gel extrudes from the mass and opens at the tip like a soft funnel, reaching for you in silence."
                ],
                "success": [
                    "The funnel settles over your head and draws you in with a slow, continuous suction, walls of cool slime gliding over your face without a single tremor of excitement.",
                    "You slide down a transparent tunnel that has no heat and no texture but cling, the column fattening as more of you vanishes into the parent mass.",
                    "Your legs follow in the same unhurried pull until you are curled inside a swollen lobe of gel that hangs from the main body, every surface pressed flush, every motion damped to nothing.",
                    "The lobe seals. The slime rests. Somewhere in the silent bulk, a slow internal current turns you once, as if checking that you fit."
                ],
            }
        ],
        "AV": [
            {
                "attempt": [
                    "The slime's trailing edge lifts and hollows into a wide, soft pocket, rotating toward you without hurry."
                ],
                "success": [
                    "The pocket settles over your head and shoulders and begins to drink you in, gel rolling up your back in a silent inversion of a swallow.",
                    "There is no thrash and no sound — only the steady advance of cool walls that leave you no purchase, packing you deeper into a rear chamber that did not exist a moment ago.",
                    "Your feet clear the rim. The pocket closes into a seamless bulge at the slime's hind mass, your shape a brief distortion that the gel patiently erases.",
                    "The mound stills. A single large bubble rises through its body and pops without noise at the surface."
                ],
            }
        ],
    },
    "digestion_complete": {
        "OV": [
            "{predator} shivers once; the {prey}-shaped thickness thins and vanishes into even gel.",
            "A slow internal swirl and {predator} is a smoother mound — {prey} unmade."
        ],
        "CV": [
            "{predator}'s hanging lobe shrinks to nothing, leaving only a wet sheen on the stone.",
            "The swollen column retracts into {predator}; {prey} is gone without a sound."
        ],
        "AV": [
            "{predator}'s hind bulge levels out stroke by silent stroke until the mass is uniform again.",
            "A slow flatten, and the last outline of {prey} dissolves into clear gel."
        ],
    },
    "npc_vore_hit": {
        "OV": [
            "{predator} rises and takes {prey} into its bulk without a sound!",
            "{predator} sheets over {prey} until only a thicker mound remains!"
        ],
        "CV": [
            "{predator} extrudes a column of gel and draws {prey} inside!",
            "{predator} funnels {prey} into a hanging lobe of silent slime!"
        ],
        "AV": [
            "{predator} hollows its trailing edge and packs {prey} into the hind mass!",
            "{predator} inverts around {prey} until the bulge smooths away!"
        ],
    },
    "npc_vore_miss": {
        "OV": [
            "{predator} surges toward {prey} and spreads uselessly across empty stone.",
            "{predator} reaches for {prey}, but the gel only spatters and reforms."
        ],
        "CV": [
            "{predator}'s funneling column misses {prey} and collapses back into the mass.",
            "{predator} extrudes toward {prey} and finds only air."
        ],
        "AV": [
            "{predator}'s hollowed edge swings past {prey} and flattens.",
            "{predator} rotates toward {prey} too slowly; {prey} is already clear."
        ],
    },
    "offscreen_vore": {
        "OV": [
            "You hear a soft, continuous wet sheet, then nothing.",
            "You hear a brief scuffle cut off by a heavy, liquid settle."
        ],
        "CV": [
            "You hear a slow suction, then a thick drop of something heavy.",
            "You hear a long, quiet draw of liquid over stone."
        ],
        "AV": [
            "You hear a wet inversion, then a single pop of a bubble.",
            "You hear something pack and seal with no voice behind it."
        ],
    },
    "offscreen_digest": {
        "OV": ["You hear a long, low settle of liquid evening out."],
        "CV": ["You hear a soft shrink of something wet, then silence."],
        "AV": ["You hear a slow flatten of heavy gel."],
    },
    "digestion_player_modal": {
        "OV": [
            {
                "phases": [
                    "Inside the slime there is no voice, no heat, and no rhythm you can call a heartbeat — only cool pressure and a translucent dark that turns the outside world into smeared light. The gel does not squeeze to hurt you. It simply refuses to leave any space that is not slime.",
                    "Your edges soften where the current touches them. Flesh thins into the same clear medium that holds you, until the distinction ends. Outside, the mound becomes a little larger, a little smoother, and still says nothing at all."
                ]
            }
        ],
        "CV": [
            {
                "phases": [
                    "The hanging lobe is a closed world of cling and silence. Slow currents turn you, press you, and thin you without passion, as if the slime were only solving a shape problem.",
                    "You run into the walls. The lobe empties of everything that was solid about you and draws back into the parent mass, leaving the stone damp and the slime unchanged in mood — because it has none."
                ]
            }
        ],
        "AV": [
            {
                "phases": [
                    "Packed in the hind chamber, you feel only even pressure and the occasional drift of a bubble past your face. The gel works without hurry, dissolving the idea of limbs before it dissolves the limbs themselves.",
                    "You become current, then clarity, then nothing distinct. The slime's outline levels. Somewhere far away, boots scrape stone. The gel does not turn to look."
                ]
            }
        ],
    },
}


FOX_ARCHER = {
    **base_combat(
        id="fox_archer",
        display_name="fox archer",
        glyph="f",
        fg=[200, 120, 60],
        alignment="evil",
        mobility="ground",
        examine=(
            "An anthro fox in travel-stained leathers, bow unstrung at their shoulder until "
            "it isn't. Their movements are economical, almost bored — the posture of someone "
            "who has cleared a hundred corridors like this one and expects you to be number "
            "one hundred and one."
        ),
        max_hp=11,
        evade=3,
        ac=1,
        accuracy=0.4,
        min_damage=1,
        max_damage=2,
        ranged_accuracy=0.7,
        ranged_min_damage=4,
        ranged_max_damage=6,
        experience_points=75,
        digestion_damage_per_tick=3,
        digest_time=5,
        abilities=[],
        spawn={"weight": 2, "min_depth": 5, "max_depth": 14, "terrain": "land"},
    ),
    "vore_narratives": {
        "OV": [
            {
                "attempt": [
                    "The fox archer steps in close with a practiced pivot, maw opening not in rage but in the calm of a routine finisher!"
                ],
                "success": [
                    "Your head is guided into a warm, well-used throat with the same neat confidence they use to nock an arrow — no flourish, no hesitation, only the sure angle that makes struggle feel like bad form.",
                    "Hands that have looted a dozen belts before this one settle at your shoulders and feed you down in measured swallows, the fox's ears flicking once as if filing you under miscellaneous encounter.",
                    "You fold into a tight, professional gut that has clearly done this work before: firm walls, efficient slime, no wasted space. Somewhere above, the fox mutters, half to themselves, \"One more for the tally.\"",
                    "Your feet clear their lips. The fox pats the taut belly once, checks their quiver out of habit, and already looks past the corridor for the next marker on the map."
                ],
            }
        ],
        "CV": [
            {
                "attempt": [
                    "The fox archer catches your wrist, spins you with a dancer's economy, and presents a sleek, well-kept length as casually as drawing steel!"
                ],
                "success": [
                    "The tip opens over your head in one clean motion — no frantic humping, only controlled pressure that walks you down the shaft like a practiced reload.",
                    "\"Stay still; this goes faster,\" they murmur, almost helpful, while hips deliver short, precise thrusts that pack you into a plush sack without a wasted motion.",
                    "You settle in a warm, ordered chamber that squeezes like good packing straps. The fox adjusts their belt over the bulge and huffs a short laugh. \"Call it a restock.\"",
                    "Your feet vanish. The fox rolls their shoulders, already counting arrows again, belly-and-sack weight treated as just another bit of kit on the march."
                ],
            }
        ],
        "AV": [
            {
                "attempt": [
                    "The fox archer turns with a neat pivot, tail lifted, as if setting up a standard control hold rather than a desperation play!"
                ],
                "success": [
                    "Their rim takes your head in a smooth stretch, hands on your hips feeding you in with the patience of someone who has finished fights this way when the bow was the wrong tool.",
                    "You slide into a hot, clenching lower gut that works in even pulls — elegant, unhurried, faintly dismissive of how hard you thrash.",
                    "\"There we go. Obstacle cleared,\" they say lightly as your feet pass the seal, already thinking about the next room's sightlines.",
                    "The fox settles their tail over a well-rounded rump, checks the corridor, and moves on with the gait of a runner who just stowed a minor problem."
                ],
            }
        ],
    },
    "digestion_complete": {
        "OV": [
            "{predator} exhales as the {prey}-bulge smooths out. \"Experience collected,\" they murmur.",
            "{predator}'s gut finishes its work with a tidy gurgle; {prey} becomes a little more fox."
        ],
        "CV": [
            "{predator} shudders once and paints the stone — then wipes their mouth and recounts arrows.",
            "{predator} empties what was {prey} with a short, practiced breath. \"Stats absorbed. Moving on.\""
        ],
        "AV": [
            "{predator}'s haunches settle as {prey} works into sleek fox-plush. \"Room clear.\"",
            "A neat series of gurgles and {predator} is lighter on their feet again — {prey} accounted for."
        ],
    },
    "npc_vore_hit": {
        "OV": [
            "{predator} steps in and swallows {prey} with the calm of a routine finisher!",
            "{predator} gulps {prey} down and pats the belly like checking a pack strap!"
        ],
        "CV": [
            "{predator} packs {prey} into their shaft with clean, economical thrusts!",
            "{predator} stows {prey} in a taut sack and is already scanning for the next target!"
        ],
        "AV": [
            "{predator} turns, feeds {prey} up their rear, and calls the corridor clear!",
            "{predator} seals {prey} away with a dancer's pivot and keeps walking!"
        ],
    },
    "npc_vore_miss": {
        "OV": [
            "{predator} reaches for {prey} and clicks their tongue when the grab fails.",
            "{predator}'s practiced lunge meets empty air; they reset stance without drama."
        ],
        "CV": [
            "{predator} tries to line {prey} up and loses the angle. \"Fine. Bow it is.\"",
            "{predator}'s grip slips; they step back and put space between you again."
        ],
        "AV": [
            "{predator} pivots for a rear take and misjudges {prey}'s footwork.",
            "{predator}'s tail flicks in annoyance as {prey} slips the hold."
        ],
    },
    "offscreen_vore": {
        "OV": [
            "You hear a short scuffle, a clean gulp, and a fox voice: \"Tally one.\"",
            "You hear practiced footsteps, then a wet swallow that does not sound rushed."
        ],
        "CV": [
            "You hear a brief, controlled series of thrusts and a muttered \"restock.\"",
            "You hear leather shift and a long, tidy suck somewhere nearby."
        ],
        "AV": [
            "You hear a pivot, a seal, and someone saying \"obstacle cleared.\"",
            "You hear an efficient packing squelch and boots already moving on."
        ],
    },
    "offscreen_digest": {
        "OV": ["You hear a tidy gurgle and a fox murmur about experience."],
        "CV": ["You hear a short shudder and the soft scrape of an arrow recounted."],
        "AV": ["You hear neat gut-work and a casual \"room clear.\""],
    },
    "digestion_player_modal": {
        "OV": [
            {
                "phases": [
                    "The fox's gut works with the same economy as their archery — firm pressure, no wasted thrashing, slime applied like a known recipe. Outside, you feel them walk, pause at a corner, and continue, your struggle filed under expected resistance from a standard enemy.",
                    "Walls close and soften you into the mix. The last thing you make out is a light pat on the belly and a quiet, almost cheerful note: \"Good fight. Stats are mine now.\""
                ]
            }
        ],
        "CV": [
            {
                "phases": [
                    "Bound in the fox's sack, you are cargo on a professional's belt. Their breathing stays even. When they speak, it is half to themselves, half to the job: loot routes, arrow count, how many encounters until camp.",
                    "The chamber milks you down to slick heat and then empties you in one controlled rush. Somewhere above, the fox already strings the bow again, lighter, fed, and unsentimental."
                ]
            }
        ],
        "AV": [
            {
                "phases": [
                    "Their lower gut holds you like a problem solved. Muscles work in clean cycles while the fox's attention is clearly elsewhere — next door, next depth, next mark on a private scoreboard.",
                    "You thin into haunch and tail-plush under a final neat clench. Boots scrape. The corridor goes on without you, and the fox does not look back."
                ]
            }
        ],
    },
}


GNOLL_MERCENARY = {
    **base_combat(
        id="gnoll_mercenary",
        display_name="gnoll mercenary",
        glyph="h",
        fg=[180, 140, 70],
        alignment="evil",
        mobility="ground",
        examine=(
            "An anthro hyena in mismatched scavenged armor, pouches bulging with other "
            "people's buckles and charms. Their eyes flick to your weapon first, your pack "
            "second, and your face almost not at all — an extraction hunter sizing up whether "
            "you are worth the fight."
        ),
        max_hp=16,
        evade=1,
        ac=2,
        accuracy=0.55,
        min_damage=4,
        max_damage=6,
        ranged_accuracy=0.45,
        ranged_min_damage=2,
        ranged_max_damage=3,
        experience_points=85,
        digestion_damage_per_tick=3,
        digest_time=5,
        abilities=[],
        spawn={"weight": 2, "min_depth": 6, "max_depth": 16, "terrain": "land"},
    ),
    "vore_narratives": {
        "OV": [
            {
                "attempt": [
                    "The gnoll mercenary rushes you maw-first, one hand already snatching at your belt as if the swallow and the looting are the same motion!"
                ],
                "success": [
                    "Hot hyena breath and a rough tongue hit your face as the jaws crank wide; a free hand yanks your pack strap hard enough to pop a buckle before your shoulders even clear their teeth.",
                    "\"Anything good in there?\" they rasp around your ribs, half laugh, half inventory check, throat muscles hauling you down while fingers keep fishing at pouches that are about to be out of reach.",
                    "You drop into a thick, greedy gut that squeezes like a thrift-store bag stuffed past capacity. Outside, the gnoll is already feeling along the outside of the bulge for the shape of a weapon hilt.",
                    "Your feet kick once past their lips. The gnoll sits back with a grunt, belly huge, and starts unbuckling whatever gear they managed to strip before you vanished — sorting loot before digestion even starts."
                ],
            }
        ],
        "CV": [
            {
                "attempt": [
                    "The gnoll hooks your collar, shoves you down, and swings a thick, scavenger-hard cock into line with the same urgency they use for a contested loot pile!"
                ],
                "success": [
                    "The tip punches over your head and sucks hard; above you the gnoll is still talking, voice strained: \"Nice boots. Those are coming with me.\"",
                    "Hips drive in short, greedy thrusts that pack you into a heavy sack while their hands keep working — unbuckling, pocketing, stuffing your things into their own pouches mid-swallow.",
                    "You curl in a musky, overstuffed chamber that flexes every time the gnoll leans to grab another item off the floor. Extraction first. You second.",
                    "Your feet pop through. The gnoll gives the sack a possessive squeeze, already counting what they gained, as if you were just the bag that held the good parts."
                ],
            }
        ],
        "AV": [
            {
                "attempt": [
                    "The gnoll spins, rump back, and grabs for your wrists — control the target, strip the kit, finish the job!"
                ],
                "success": [
                    "Their rim takes your head while a hand strips a ring or charm from your fingers with professional spite. \"Mine now,\" they pant, and shove.",
                    "You are worked into a thick lower gut in rough, efficient pushes; the gnoll's free hand keeps looting what it can reach until your arms are too deep to rob.",
                    "Sealed to the ankles, then the toes, you hang as a heavy haunch-bulge while the mercenary crouches to sweep the floor for anything that fell mid-fight.",
                    "They stand, overloaded with new gear and new weight, laughing once through their teeth. \"Extraction complete.\""
                ],
            }
        ],
    },
    "digestion_complete": {
        "OV": [
            "{predator} pats a smoother belly and jingles a pouch. \"Loot's better than the meal.\"",
            "{predator}'s gut finishes {prey}; the gnoll is already re-sorting scavenged gear."
        ],
        "CV": [
            "{predator} empties what was {prey} and checks a stolen buckle for quality.",
            "{predator} shudders, sprays, and goes right back to inventorying pouches."
        ],
        "AV": [
            "{predator}'s rump settles as {prey} becomes haunch; a scavenged charm gets a satisfied sniff.",
            "A heavy gurgle and {predator} rolls their shoulders under a fuller pack. \"Worth it.\""
        ],
    },
    "npc_vore_hit": {
        "OV": [
            "{predator} gulps {prey} and strips a pouch on the way down!",
            "{predator} swallows {prey} whole while already pocketing loose gear!"
        ],
        "CV": [
            "{predator} packs {prey} into their cock and loots with both hands free a moment later!",
            "{predator} stows {prey} in a heavy sack and goes for the dropped pack!"
        ],
        "AV": [
            "{predator} draws {prey} up their rear mid-looting frenzy!",
            "{predator} seals {prey} away and crouches to sweep the floor for scraps!"
        ],
    },
    "npc_vore_miss": {
        "OV": [
            "{predator} snaps at {prey} and grabs only a strap that tears free.",
            "{predator}'s loot-handed lunge misses; they snarl at the wasted grab."
        ],
        "CV": [
            "{predator} tries to pin {prey} for a shaft-take and loses the collar grip.",
            "{predator} lunges hips-first; {prey} slips, and the gnoll curses the empty hands."
        ],
        "AV": [
            "{predator} backs onto empty air and nearly drops a half-stolen pouch.",
            "{predator}'s rear rush fails; they scramble to keep hold of the loot they already took."
        ],
    },
    "offscreen_vore": {
        "OV": [
            "You hear a scuffle, a wet gulp, and a hyena voice asking about gear quality.",
            "You hear pouches jingle hard, then a long, greedy swallow."
        ],
        "CV": [
            "You hear buckles popping and a thick, straining suck.",
            "You hear someone laugh about boots, then a heavy packing sound."
        ],
        "AV": [
            "You hear a rough seal and the clatter of sorted loot on stone.",
            "You hear \"extraction complete\" after a wet, final squelch."
        ],
    },
    "offscreen_digest": {
        "OV": ["You hear a gurgle and the shake of a re-sorted pouch."],
        "CV": ["You hear a splat and someone appraising a stolen buckle."],
        "AV": ["You hear heavy gut-work and a satisfied scavenger snort."],
    },
    "digestion_player_modal": {
        "OV": [
            {
                "phases": [
                    "The gnoll's gut is crowded and restless, walls shoving you around while the mercenary outside keeps moving — kneeling, standing, jingling metal as they reorganize what used to be yours. You are not the prize. You are the bag that came with the prize.",
                    "Slime and pressure finish what the fight started. You soften into the mix while the gnoll laughs at something small and valuable in their palm. When the belly smooths, they are already walking toward the next poor soul with a full pack."
                ]
            }
        ],
        "CV": [
            {
                "phases": [
                    "From inside the sack you hear inventory more clearly than your own pulse: clasps, coins, the scrape of a blade being tested for edge. The gnoll's hips twitch whenever they find something good, grinding you without looking down.",
                    "The chamber empties you in a thick rush. Above, the mercenary wipes off, cinches a stolen belt, and moves on heavier in gear and lighter in conscience."
                ]
            }
        ],
        "AV": [
            {
                "phases": [
                    "Wedged in their lower gut, you feel every crouch as they loot the floor. The mercenary talks to themselves about resale value while their insides talk you into slurry.",
                    "You become haunch and heat. Outside, a charm clinks into a pouch. Extraction is over. You are not listed on the manifest."
                ]
            }
        ],
    },
}


ROC = {
    **base_combat(
        id="roc",
        display_name="roc",
        glyph="R",
        fg=[160, 140, 100],
        alignment="evil",
        mobility="flyer",
        examine=(
            "A raptor large enough to make you feel incorrectly sized for the world — roughly "
            "three times your height at the shoulder of its wing, feathers the color of storm "
            "cloud and dry stone. Its eye tracks you with the bored precision of high nobility "
            "noticing a pebble in the path."
        ),
        max_hp=24,
        evade=2,
        ac=3,
        accuracy=0.6,
        min_damage=6,
        max_damage=9,
        experience_points=120,
        digestion_damage_per_tick=4,
        digest_time=5,
        abilities=[],
        spawn={"weight": 1, "min_depth": 10, "max_depth": 22, "terrain": "land"},
    ),
    "vore_narratives": {
        "OV": [
            {
                "attempt": [
                    "The roc's head dips on a neck like a crane-arm, beak parting with ceremonial calm — not a lunge so much as a collection."
                ],
                "success": [
                    "The beak closes around your torso with careful strength, lifting you off the stone as if you were a wrapped parcel. Wind from a single wingbeat flattens your clothes.",
                    "You are tilted back and fed into a vast, feather-warm throat that swallows in slow, dignified pulls; the roc's eye never widens, never brightens — only notes that the cargo is secured.",
                    "Hall stone falls away beneath you. Inside, the crop and belly open into a cavernous, swaying chamber lined with heat and soft slime, your whole body a minor weight under the keel of a sky-creature.",
                    "The last wing-assisted gulp seats you fully. The roc levels out in the air of the vaulted hall, belly deep and round, already looking for a higher perch on which to finish its meal in peace."
                ],
            }
        ],
        "CV": [
            {
                "attempt": [
                    "The roc banks, talons hooking your shoulders, and a thick avian length unsheathes along its belly with aristocratic indifference!"
                ],
                "success": [
                    "Suspended, you are aligned and taken in a single long draw that feels less like lust than logistics — the shaft stretches, claims, and files you downward.",
                    "Wingbeats rock you as you slide into a heavy, down-soft sack that sways under the roc like a cargo sling, walls plush and absolute.",
                    "Your feet clear the tip. The bird adjusts its grip on the empty air, feathers settling, the bulge beneath it treated as a solved problem of mass and balance.",
                    "It climbs a thermal of dungeon heat, sack full, gaze already elsewhere — you are undercarriage, not audience."
                ],
            }
        ],
        "AV": [
            {
                "attempt": [
                    "The roc turns in the air, tail fan spreading, and presents a huge feathered rear with the poise of a court gesture!"
                ],
                "success": [
                    "Talons hold you steady while the rim settles over your head and begins a slow, powerful take, each clench a decree rather than a thrash.",
                    "You are drawn into a vast lower gut that smells of warm down and sky, muscles working in long strokes that leave no doubt who owns the vertical space of the hall.",
                    "Sealed to the soles, you hang as a dignified swelling under the roc's tail as it rights itself and resumes altitude.",
                    "A soft, contemptuous croon vibrates through the chamber — not for you, but for the satisfaction of a clean acquisition."
                ],
            }
        ],
    },
    "digestion_complete": {
        "OV": [
            "{predator} settles on a high ledge as the {prey}-keel smooths into deep breast-fat.",
            "A long aerial gurgle and {predator}'s belly trims back; {prey} is roc now."
        ],
        "CV": [
            "{predator} shudders mid-glide and leaves a pale trail far below where {prey} used to be.",
            "{predator}'s sack drains in one noble clench; the bird flies lighter."
        ],
        "AV": [
            "{predator}'s tail-line streamlines as {prey} becomes heavy rump and muscle.",
            "A rolling sky-gurgle and the last of {prey} is court-fat under {predator}'s fan."
        ],
    },
    "npc_vore_hit": {
        "OV": [
            "{predator} collects {prey} in its beak and swallows them like stowed cargo!",
            "{predator} lifts {prey} and feeds them down a throat built for larger prizes!"
        ],
        "CV": [
            "{predator} slings {prey} into a swinging avian sack mid-flight!",
            "{predator} draws {prey} under its keel with aristocratic calm!"
        ],
        "AV": [
            "{predator} takes {prey} under its tail fan in one long aerial pull!",
            "{predator} seals {prey} into a vast lower gut and climbs!"
        ],
    },
    "npc_vore_miss": {
        "OV": [
            "{predator}'s beak snaps shut on empty air; a wing-buffet nearly knocks {prey} down.",
            "{predator} dips to collect {prey} and misjudges the dodge."
        ],
        "CV": [
            "{predator}'s talons scrape stone as {prey} slips the line-up.",
            "{predator} banks for a shaft-take and finds only a near miss."
        ],
        "AV": [
            "{predator}'s rear presentation meets empty space; it rights itself with offended dignity.",
            "{predator} turns too wide; {prey} is already under cover."
        ],
    },
    "offscreen_vore": {
        "OV": [
            "You hear a huge wingbeat, a careful gulp, and feathers settling high up.",
            "You hear something large collected off the floor, then a long swallow."
        ],
        "CV": [
            "You hear talons scrape and a deep, swinging wet take.",
            "You hear a heavy sack-sound under wing noise."
        ],
        "AV": [
            "You hear a fan of feathers and a long, sealing pull.",
            "You hear an aerial croon after a thick, final squelch."
        ],
    },
    "offscreen_digest": {
        "OV": ["You hear a high-ledge gurgle and a satisfied wing-settle."],
        "CV": ["You hear a distant mid-air shudder and dripping far below."],
        "AV": ["You hear deep tail-line churning that slowly streamlines."],
    },
    "digestion_player_modal": {
        "OV": [
            {
                "phases": [
                    "The roc's belly is a warm cathedral that sways with every wingbeat. You are small in it by design — cargo under a keel, listened to only as a shift of mass. Outside, the bird chooses a perch as if selecting a seat at court.",
                    "Slime and pressure reduce you to heat and then to fat along a breast already built for long flights. The roc preens once, heavier, and does not think of you as anything that had a name."
                ]
            }
        ],
        "CV": [
            {
                "phases": [
                    "The sack under the roc is a swinging cradle of down-heat and absolute containment. Flight turns you. Landing settles you. The bird's pulse is a slow drum of something that never needed to hurry to win.",
                    "You thin into the churn and leave as a pale trail far beneath a wing-shadow. The roc trims its weight and climbs again, schedule uninterrupted."
                ]
            }
        ],
        "AV": [
            {
                "phases": [
                    "Deep under the tail fan, every adjustment of flight wrings the chamber around you. You are not prey in a story. You are ballast being converted to better ballast.",
                    "The last of you streamlines into muscle and plush. The roc's silhouette cleans itself in the air, noble and complete."
                ]
            }
        ],
    },
}


OWL_MAGE = {
    **base_combat(
        id="owl_mage",
        display_name="owl mage",
        glyph="M",
        fg=[200, 200, 220],
        alignment="evil",
        mobility="ground",
        examine=(
            "An anthro owl in layered scholar's robes, feathers dusted with chalk and old "
            "spell residue. A small focus crystal hangs at their breast. Their head tips with "
            "bright, academic interest — not hunger first, but the look of someone who has "
            "found a specimen."
        ),
        max_hp=13,
        evade=2,
        ac=1,
        accuracy=0.5,
        min_damage=2,
        max_damage=4,
        ranged_accuracy=0.55,
        ranged_min_damage=3,
        ranged_max_damage=5,
        experience_points=100,
        digestion_damage_per_tick=3,
        digest_time=6,
        abilities=[],
        spawn={"weight": 1, "min_depth": 12, "max_depth": 24, "terrain": "land"},
    ),
    "vore_narratives": {
        "OV": [
            {
                "attempt": [
                    "The owl mage flicks a claw through a tight sigil; the air pinches, and the world lurches as you shrink toward coin-size in their open palm!"
                ],
                "success": [
                    "Suddenly the owl's face is a moon above you — enormous eyes, enormous beak — while their voice stays mild and delighted: \"Oh! I've never eaten one of your kind before.\"",
                    "You are tipped from the palm into a cavernous, feather-soft maw. What was a normal swallow for them is a fall through a hot, ribbed tunnel that could hold a cathedral relative to your new scale.",
                    "You tumble into a stomach like a round study hall, walls flexing in gentle researcher's pulses as the owl's muffled hum vibrates the chamber. \"Wonder what you're like,\" they muse, already taking mental notes.",
                    "Outside, the owl dabs their beak with a sleeve, belly only slightly rounded for their size, and peers at a floating mote of residual spell-light where you used to stand tall."
                ],
            }
        ],
        "CV": [
            {
                "attempt": [
                    "A reduction seal snaps shut around you; the owl mage lifts your tiny form with two claws and aligns you with a shaft that might as well be a tower!"
                ],
                "success": [
                    "\"Sample acquisition,\" they announce cheerfully as the tip swallows your whole shrunken body in one polite sip.",
                    "You rocket down a hot, ridged tunnel scaled for someone who was never meant to be this small, landing in a plush, rolling sack that tosses you like a pea in a drum.",
                    "The owl adjusts their robes over a barely-there bulge and makes a soft hoot of scientific pleasure. \"Notes later. Digestion first, of course.\"",
                    "Your entire world is heat, bounce, and the distant scratch of a quill as they jot something mid-process, utterly at ease."
                ],
            }
        ],
        "AV": [
            {
                "attempt": [
                    "The owl mage shrinks you with a precise word, then turns and offers a rear that, at your new size, is a cliff-face of soft feathers and intent!"
                ],
                "success": [
                    "They place you at the rim like setting a specimen on a tray; the take is gentle, scholarly, and completely irresistible at this scale.",
                    "You slide into a lower gut that feels continental, walls rolling you along while the owl remarks, half to a mental journal, \"Texture: lively. Resistance: temporary.\"",
                    "Sealed in a chamber that could lose you in a fold, you hear them smooth their robes and return to an idle cantrip as if the experiment were already past the exciting part.",
                    "A soft hoot. A pat somewhere far above your whole existence. The study continues."
                ],
            }
        ],
    },
    "digestion_complete": {
        "OV": [
            "{predator} hums as a tiny {prey}-weight vanishes. \"Fascinating composition.\"",
            "{predator}'s barely-rounded belly settles; {prey} is data and a little owl-warmth."
        ],
        "CV": [
            "{predator} shivers once and murmurs, \"Sample fully processed.\"",
            "{predator} empties a trivial amount of what was {prey} and returns to their notes."
        ],
        "AV": [
            "{predator}'s posture straightens as {prey} becomes a forgettable calorie. \"Hmm.\"",
            "A soft internal finish; {predator} scratches a final line in the air with a claw."
        ],
    },
    "npc_vore_hit": {
        "OV": [
            "{predator} shrinks {prey} and tips them into a scholarly maw!",
            "{predator} reduces {prey} and swallows the specimen with bright-eyed interest!"
        ],
        "CV": [
            "{predator} micro-sizes {prey} and sips them down like a lab sample!",
            "{predator} seals a reduction spell and packs {prey} into a sack the size of a thought!"
        ],
        "AV": [
            "{predator} shrinks {prey} and places them for a careful rear take!",
            "{predator} runs a quick experiment: tiny {prey}, vast owl, predictable result!"
        ],
    },
    "npc_vore_miss": {
        "OV": [
            "{predator}'s shrink-sign misfires; {prey} staggers but stays full-size.",
            "{predator} reaches for a reduced {prey} that never quite finished shrinking."
        ],
        "CV": [
            "{predator}'s reduction takes, but {prey} tumbles from the claws before the sip.",
            "{predator} fumbles the tiny form; spell-light scatters as {prey} rolls free."
        ],
        "AV": [
            "{predator} shrinks {prey} and then tips them past the intended rim.",
            "{predator}'s careful placement fails; a mote-sized {prey} hits the floor running."
        ],
    },
    "offscreen_vore": {
        "OV": [
            "You hear a tight magical pinch, a delighted hoot, and a tiny splash of a swallow.",
            "You hear: \"Never eaten one of your kind!\" — then a soft, scholarly gulp."
        ],
        "CV": [
            "You hear a reduction seal and a polite, absurdly small suck.",
            "You hear a quill scratch and a muffled \"sample acquisition.\""
        ],
        "AV": [
            "You hear spell-words, a soft placement, and a long careful take.",
            "You hear an academic hoot after a tiny, final seal."
        ],
    },
    "offscreen_digest": {
        "OV": ["You hear a contented hum and the words \"fascinating composition.\""],
        "CV": ["You hear a small shiver and \"sample fully processed.\""],
        "AV": ["You hear robes settle and a thoughtful owl \"hmm.\""],
    },
    "digestion_player_modal": {
        "OV": [
            {
                "phases": [
                    "At this size the owl's stomach is weather. Warm fronts of slime roll over you while a voice outside lectures no one in particular about novelty and method. You are not a rival. You are a first-time meal of an interesting category.",
                    "The walls reduce you further — not with another spell, but with ordinary digestion that, scaled to you, is a cataclysm. When it ends, the owl flexes a claw, heavier by a thought, and files the result under experience."
                ]
            }
        ],
        "CV": [
            {
                "phases": [
                    "The sack tosses your entire body like a bead. Outside, pages turn. The owl's pulse is a giant's drum. Curiosity without cruelty is still absolute.",
                    "You dissolve into heat the owl will barely notice on the scale. A note is finished. The experiment is closed."
                ]
            }
        ],
        "AV": [
            {
                "phases": [
                    "Lost in a fold of lower gut, you feel the mage sit, stand, and cast minor lights while you are processed as thoroughly as any reagent.",
                    "You become nothing the robes need to adjust for. Somewhere, a crystal focus catches the light. The owl has already moved on to the next question."
                ]
            }
        ],
    },
}


def deep_stub(
    *,
    id: str,
    display_name: str,
    glyph: str,
    fg: list[int],
    mobility: str,
    examine: str,
    max_hp: int,
    evade: int,
    ac: int,
    accuracy: float,
    min_damage: int,
    max_damage: int,
    xp: int,
    dig: int,
    digest_time: int,
    min_depth: int,
    max_depth: int,
    weight: int,
) -> dict:
    block = stub_block(display_name)
    return {
        **base_combat(
            id=id,
            display_name=display_name,
            glyph=glyph,
            fg=fg,
            alignment="evil",
            mobility=mobility,
            examine=examine,
            max_hp=max_hp,
            evade=evade,
            ac=ac,
            accuracy=accuracy,
            min_damage=min_damage,
            max_damage=max_damage,
            experience_points=xp,
            digestion_damage_per_tick=dig,
            digest_time=digest_time,
            spawn={
                "weight": weight,
                "min_depth": min_depth,
                "max_depth": max_depth,
                "terrain": "land",
            },
        ),
        **block,
    }


TARANTULA = deep_stub(
    id="tarantula",
    display_name="tarantula",
    glyph="S",
    fg=[90, 70, 50],
    mobility="ground",
    examine=(
        "[placeholder] A heavy, velvet-haired spider the size of a wolf. Theme reserved "
        "for a later writing pass — stats and stub vore only."
    ),
    max_hp=14,
    evade=1,
    ac=2,
    accuracy=0.55,
    min_damage=3,
    max_damage=5,
    xp=70,
    dig=3,
    digest_time=6,
    min_depth=4,
    max_depth=12,
    weight=2,
)

WYVERN = deep_stub(
    id="wyvern",
    display_name="wyvern",
    glyph="y",
    fg=[100, 160, 90],
    mobility="flyer",
    examine=(
        "[placeholder] A lean winged reptile, two-legged, mean-eyed. Full theme TBD — "
        "deep-floor pressure placeholder."
    ),
    max_hp=28,
    evade=2,
    ac=3,
    accuracy=0.6,
    min_damage=7,
    max_damage=10,
    xp=140,
    dig=5,
    digest_time=5,
    min_depth=18,
    max_depth=40,
    weight=1,
)

DRAKE = deep_stub(
    id="drake",
    display_name="drake",
    glyph="d",
    fg=[140, 90, 50],
    mobility="ground",
    examine=(
        "[placeholder] A wingless dragon-kin, low-slung and heavily scaled. Theme TBD — "
        "deep ramp placeholder."
    ),
    max_hp=34,
    evade=1,
    ac=4,
    accuracy=0.6,
    min_damage=8,
    max_damage=12,
    xp=160,
    dig=5,
    digest_time=5,
    min_depth=22,
    max_depth=50,
    weight=1,
)

GRYPHON = deep_stub(
    id="gryphon",
    display_name="gryphon",
    glyph="g",
    fg=[190, 160, 80],
    mobility="flyer",
    examine=(
        "[placeholder] Eagle forequarters, lion hind — dungeon-scale chimera. Theme TBD."
    ),
    max_hp=32,
    evade=2,
    ac=3,
    accuracy=0.62,
    min_damage=8,
    max_damage=11,
    xp=155,
    dig=5,
    digest_time=5,
    min_depth=28,
    max_depth=60,
    weight=1,
)

DRAGON = deep_stub(
    id="dragon",
    display_name="dragon",
    glyph="D",
    fg=[200, 60, 40],
    mobility="ground",
    examine=(
        "[placeholder] A true dragon, or close enough that the distinction will not help "
        "you. Soft deep-floor stopper — theme TBD; meant to end runs that push too far."
    ),
    max_hp=55,
    evade=2,
    ac=5,
    accuracy=0.65,
    min_damage=12,
    max_damage=18,
    xp=250,
    dig=7,
    digest_time=4,
    min_depth=40,
    max_depth=1000,
    weight=1,
)


def main() -> None:
    data = json.loads(ENTITIES.read_text(encoding="utf-8"))
    entities: list[dict] = data["entities"]
    by_id = {e["id"]: e for e in entities}

    # Replace / update known
    by_id["cave_rat"] = CAVE_RAT

    spider = by_id["giant_spider"]
    spider["spawn"]["weight"] = 0
    spider["examine"] = (
        "[deprecated] Former stock filler; spawn weight 0. Prefer tarantula. "
        "Kept so old saves soft-load the id."
    )
    spider["placeholder"] = True

    for ent in (
        SLIME,
        TARANTULA,
        FOX_ARCHER,
        GNOLL_MERCENARY,
        ROC,
        OWL_MAGE,
        WYVERN,
        DRAKE,
        GRYPHON,
        DRAGON,
    ):
        by_id[ent["id"]] = ent

    # Preserve order: original order for existing, append new at end in design order
    order = [
        "bat",
        "wolf",
        "knight",
        "rabbit",
        "shark",
        "cave_rat",
        "giant_spider",
        "kobold",
        "tunnel_slug",
        "slime",
        "tarantula",
        "fox_archer",
        "gnoll_mercenary",
        "roc",
        "owl_mage",
        "wyvern",
        "drake",
        "gryphon",
        "dragon",
    ]
    data["entities"] = [by_id[i] for i in order if i in by_id]
    # Any unexpected extras
    for eid, ent in by_id.items():
        if eid not in order:
            data["entities"].append(ent)

    ENTITIES.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(data['entities'])} entities to {ENTITIES}")


if __name__ == "__main__":
    main()
