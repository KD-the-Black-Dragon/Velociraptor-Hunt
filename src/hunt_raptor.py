"""One velociraptor: tank body, fair cone FOV, profiling mind."""

from __future__ import annotations

import random

import attrs

from src.hunt_facing import facing_toward
from src.hunt_fov import visible_tiles
from src.hunt_map import HuntMap, load_paddock_config
from src.hunt_stance import Gait

RAPTOR_ACTOR = "raptor"


@attrs.define
class RaptorMind:
    last_seen_x: int | None = None
    last_seen_y: int | None = None
    last_seen_facing: int | None = None
    last_seen_aim: int = 0
    observations: int = 0
    rotate_hits: int = 0
    stare_streak: int = 0
    edge_hits: int = 0
    sound_events: int = 0
    sound_reacts: int = 0
    last_obs_facing: int | None = None
    intent: str = "wander"
    thought: str = ""
    fix_x: int | None = None
    fix_y: int | None = None
    fix_aut: float = 0.0
    hunter_busy: int = 0
    last_seen_heading: float | None = None
    last_seen_cone: int = 12
    last_seen_half: float = 55.0
    last_seen_grass: int = 2
    last_seen_blind: int = 0
    sweep_facings: tuple[int, ...] = ()
    last_heard_x: int | None = None
    last_heard_y: int | None = None
    last_heard_aut: float = -99.0
    burn_x: int | None = None
    burn_y: int | None = None
    burn_aut: float = -99.0
    hide_sit: int = 0
    stalk_watch: int = 0
    peek_key: str = ""
    last_bait_aut: float = -99.0


@attrs.define
class HuntRaptor:
    x: int
    y: int
    facing: int = 0
    hp: int = 100
    max_hp: int = 100
    visible: set[tuple[int, int]] = attrs.field(factory=set)
    mind: RaptorMind = attrs.field(factory=RaptorMind)
    gait: Gait = Gait.WALK
    last_move_facing: int | None = None
    shown_health: str | None = None
    last_aut: float = 0.8
    speed_mult: float = 2.0
    belief: object | None = None
    scanned_aut: object | None = None

    @property
    def tranquilized(self) -> bool:
        return self.hp <= 0

    def refresh_fov(
        self,
        mmap: HuntMap,
        *,
        range_penalty: int = 0,
        grass_see_through: int = 2,
        cone_bonus: int = 0,
    ) -> None:
        cfg = load_paddock_config()
        cone = max(2, cfg.raptor_cone_range + max(0, cone_bonus) - max(0, range_penalty))
        self.visible = visible_tiles(
            mmap,
            origin_x=self.x,
            origin_y=self.y,
            facing=self.facing,
            cone_range=cone,
            half_degrees=cfg.raptor_cone_half_degrees,
            grass_see_through=grass_see_through,
        )

    def sees(self, x: int, y: int) -> bool:
        return (x, y) in self.visible

    def record_motion(self, origin_x: int, origin_y: int) -> None:
        """After a turn: keep last step direction, or clear it if this turn did not move."""
        if (self.x, self.y) == (origin_x, origin_y):
            self.last_move_facing = None
            return
        self.last_move_facing = facing_toward(origin_x, origin_y, self.x, self.y)


def pick_raptor_spawn(
    mmap: HuntMap,
    player_x: int,
    player_y: int,
    rng: random.Random,
) -> tuple[int, int, int]:
    """Walkable tile, prefer far from the hunter. Facing toward the center."""
    best: list[tuple[int, int, int]] = []
    best_d = -1
    for y in range(mmap.height):
        for x in range(mmap.width):
            if not mmap.walkable(x, y):
                continue
            if x == player_x and y == player_y:
                continue
            d = max(abs(x - player_x), abs(y - player_y))
            if d > best_d:
                best_d = d
                best = [(x, y, d)]
            elif d == best_d:
                best.append((x, y, d))
    if not best:
        return mmap.center_x, mmap.center_y, 0
    x, y, _ = rng.choice(best)
    facing = facing_toward(x, y, mmap.center_x, mmap.center_y)
    return x, y, facing


def raptor_try_step(
    raptor: HuntRaptor,
    mmap: HuntMap,
    dx: int,
    dy: int,
    *,
    blocked: set[tuple[int, int]],
) -> bool:
    nx, ny = raptor.x + dx, raptor.y + dy
    if not mmap.walkable(nx, ny) or (nx, ny) in blocked:
        return False
    raptor.x = nx
    raptor.y = ny
    return True


def stub_raptor_act(
    raptor: HuntRaptor,
    mmap: HuntMap,
    *,
    hunter_x: int,
    hunter_y: int,
    rng: random.Random,
    heard_xy: tuple[int, int] | None = None,
    range_penalty: int = 0,
) -> None:
    """PR4-compatible wrapper around the PR9 mind (defaults: no HUD, hip rifle)."""
    from src.hunt_ai import RaptorSense, raptor_act
    from src.hunt_clock import RingState

    raptor_act(
        raptor,
        mmap,
        sense=RaptorSense(
            hunter_x=hunter_x,
            hunter_y=hunter_y,
            hunter_facing=0,
            hunter_aim_depth=0,
            hunter_weapon_id="rifle",
            hunter_gait="walk",
            hunter_sees_raptor=False,
            ring=RingState.CLOSE,
            hunter_ring=0.0,
            raptor_ring=0.0,
            clock_remaining=80.0,
            heard_xy=heard_xy,
        ),
        rng=rng,
        range_penalty=range_penalty,
    )
