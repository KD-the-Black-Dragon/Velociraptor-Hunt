"""Path/Smite magazine helpers for RangeN/SmiteN NPCs."""

from __future__ import annotations

from tcod.ecs import Entity

from src.components import Abilities, Alignment, NPCAlignment, RangedMagazine
from src.data.ability_parser import RangeAbility, SmiteAbility
from src.data.depth_scaling_config import DifficultyProfile


def entity_has_path_or_smite(entity: Entity) -> bool:
    abilities = entity.components.get(Abilities)
    if abilities is None:
        return False
    return any(
        isinstance(parsed, (RangeAbility, SmiteAbility)) for parsed in abilities.parsed
    )


def max_shots_for_alignment(
    alignment: Alignment, profile: DifficultyProfile
) -> int:
    if alignment == Alignment.GOOD:
        return profile.good_ranged_shots
    return profile.evil_ranged_shots


def attach_ranged_magazine(entity: Entity, *, maximum: int) -> RangedMagazine:
    """Attach or replace magazine; current starts full (clamped)."""
    maximum = max(1, int(maximum))
    mag = RangedMagazine(current=maximum, maximum=maximum)
    entity.components[RangedMagazine] = mag
    return mag


def ensure_ranged_magazine(entity: Entity, *, maximum: int) -> RangedMagazine | None:
    """Attach magazine when entity has RangeN/SmiteN; otherwise leave untouched."""
    if not entity_has_path_or_smite(entity):
        return None
    existing = entity.components.get(RangedMagazine)
    if existing is not None:
        return existing
    return attach_ranged_magazine(entity, maximum=maximum)


def magazine_for(entity: Entity) -> RangedMagazine | None:
    return entity.components.get(RangedMagazine)


def can_spend_ranged_shot(entity: Entity) -> bool:
    mag = magazine_for(entity)
    return mag is not None and mag.current >= 1


def spend_ranged_shot(entity: Entity) -> bool:
    """Spend one shot if available. Returns True when spent."""
    mag = magazine_for(entity)
    if mag is None or mag.current < 1:
        return False
    mag.current -= 1
    return True


def try_ranged_reload(entity: Entity) -> bool:
    """Recover +1 shot up to maximum. Silent. Returns True when reloaded."""
    mag = magazine_for(entity)
    if mag is None:
        return False
    if mag.current >= mag.maximum:
        return False
    mag.current = min(mag.maximum, mag.current + 1)
    return True


def resolve_magazine_maximum_for_entity(
    entity: Entity, profile: DifficultyProfile
) -> int:
    alignment_comp = entity.components.get(NPCAlignment)
    alignment = (
        alignment_comp.alignment if alignment_comp is not None else Alignment.EVIL
    )
    return max_shots_for_alignment(alignment, profile)
