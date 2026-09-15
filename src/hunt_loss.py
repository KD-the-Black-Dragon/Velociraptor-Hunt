"""Swallow angle, spectacle lines, and belly/digest timing."""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path

import attrs

from src.constants import DATA_DIR
from src.hunt_facing import facing_toward

HUNT_LOSS_PATH = DATA_DIR / "hunt_loss.json"

POST_SWALLOW_DIGEST = "digest"
POST_SWALLOW_ENDOSOMA = "endosoma"

_DEFAULT_SWALLOW = ("You are swallowed whole.",)
_DEFAULT_DIGEST_PATH = ("The raptor digests you.",)
_DEFAULT_ENDOSOMA_PATH = (
    "The raptor enjoys keeping you within her belly for a long time.",
)
_DEFAULT_ENDOSOMA_SWALLOW = ("The raptor swallows you whole.",)


def normalize_post_swallow(value: str | None) -> str:
    if isinstance(value, str) and value.strip().lower() == POST_SWALLOW_ENDOSOMA:
        return POST_SWALLOW_ENDOSOMA
    return POST_SWALLOW_DIGEST


@attrs.define
class HuntNarrativeDecks:
    """Process-lifetime shuffle bags: each path once, then reshuffle."""

    remaining: dict[str, list[int]] = attrs.field(factory=dict)

    def draw(
        self,
        pool_id: str,
        paths: tuple[tuple[str, ...], ...],
        rng: random.Random,
    ) -> tuple[str, ...]:
        if not paths:
            return ()
        bag = self.remaining.get(pool_id)
        if not bag:
            bag = list(range(len(paths)))
            rng.shuffle(bag)
            self.remaining[pool_id] = bag
        idx = bag.pop(0)
        if idx >= len(paths):
            idx = 0
        return paths[idx]


@attrs.define(frozen=True)
class HuntLossConfig:
    belly_turns: int
    belly_step_chance: float
    swallow_front: tuple[str, ...]
    swallow_side: tuple[str, ...]
    swallow_behind: tuple[str, ...]
    digest_paths: tuple[tuple[str, ...], ...]
    endosoma_paths: tuple[tuple[str, ...], ...]
    endosoma_swallow_front: tuple[tuple[str, ...], ...]
    endosoma_swallow_side: tuple[tuple[str, ...], ...]
    endosoma_swallow_behind: tuple[tuple[str, ...], ...]

    @property
    def digest(self) -> tuple[str, ...]:
        if self.digest_paths:
            return self.digest_paths[0]
        return _DEFAULT_DIGEST_PATH


def attack_angle(
    hunter_x: int,
    hunter_y: int,
    hunter_facing: int,
    raptor_x: int,
    raptor_y: int,
) -> str:
    """front / side / behind relative to the hunter's facing."""
    toward = facing_toward(hunter_x, hunter_y, raptor_x, raptor_y)
    diff = min((toward - hunter_facing) % 8, (hunter_facing - toward) % 8)
    if diff == 0:
        return "front"
    if diff >= 3:
        return "behind"
    return "side"


def _as_lines(raw: object, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(raw, list) and raw and all(isinstance(x, str) for x in raw):
        return tuple(str(x) for x in raw)
    return fallback


def _as_paths(raw: object, fallback: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    if isinstance(raw, list) and raw:
        if isinstance(raw[0], list):
            paths = tuple(
                tuple(str(x) for x in path)
                for path in raw
                if isinstance(path, list) and path
            )
            if paths:
                return paths
        elif isinstance(raw[0], str):
            return (tuple(str(x) for x in raw),)
    return (fallback,)


@lru_cache(maxsize=8)
def load_hunt_loss(path: Path | None = None) -> HuntLossConfig:
    p = path if path is not None else HUNT_LOSS_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    digest_legacy = _as_lines(raw.get("digest"), _DEFAULT_DIGEST_PATH)
    digest_paths = _as_paths(raw.get("digest_paths"), digest_legacy)
    return HuntLossConfig(
        belly_turns=int(raw.get("belly_turns", 6)),
        belly_step_chance=float(raw.get("belly_step_chance", 0.5)),
        swallow_front=_as_lines(raw.get("swallow_front"), _DEFAULT_SWALLOW),
        swallow_side=_as_lines(raw.get("swallow_side"), _DEFAULT_SWALLOW),
        swallow_behind=_as_lines(raw.get("swallow_behind"), _DEFAULT_SWALLOW),
        digest_paths=digest_paths,
        endosoma_paths=_as_paths(raw.get("endosoma_paths"), _DEFAULT_ENDOSOMA_PATH),
        endosoma_swallow_front=_as_paths(
            raw.get("endosoma_swallow_front"), _DEFAULT_ENDOSOMA_SWALLOW,
        ),
        endosoma_swallow_side=_as_paths(
            raw.get("endosoma_swallow_side"), _DEFAULT_ENDOSOMA_SWALLOW,
        ),
        endosoma_swallow_behind=_as_paths(
            raw.get("endosoma_swallow_behind"), _DEFAULT_ENDOSOMA_SWALLOW,
        ),
    )


def swallow_lines(angle: str, cfg: HuntLossConfig | None = None) -> tuple[str, ...]:
    cfg = cfg if cfg is not None else load_hunt_loss()
    if angle == "front":
        return cfg.swallow_front
    if angle == "behind":
        return cfg.swallow_behind
    return cfg.swallow_side


def pick_swallow_lines(
    angle: str,
    *,
    stance: str,
    decks: HuntNarrativeDecks,
    rng: random.Random,
    cfg: HuntLossConfig | None = None,
) -> tuple[str, ...]:
    cfg = cfg if cfg is not None else load_hunt_loss()
    if normalize_post_swallow(stance) != POST_SWALLOW_ENDOSOMA:
        return swallow_lines(angle, cfg)
    if angle == "front":
        pool, pool_id = cfg.endosoma_swallow_front, "endosoma_swallow_front"
    elif angle == "behind":
        pool, pool_id = cfg.endosoma_swallow_behind, "endosoma_swallow_behind"
    else:
        pool, pool_id = cfg.endosoma_swallow_side, "endosoma_swallow_side"
    return decks.draw(pool_id, pool, rng)


def pick_post_belly_lines(
    *,
    stance: str,
    decks: HuntNarrativeDecks,
    rng: random.Random,
    cfg: HuntLossConfig | None = None,
) -> tuple[str, ...]:
    cfg = cfg if cfg is not None else load_hunt_loss()
    if normalize_post_swallow(stance) == POST_SWALLOW_ENDOSOMA:
        return decks.draw("endosoma_paths", cfg.endosoma_paths, rng)
    return decks.draw("digest_paths", cfg.digest_paths, rng)
