"""Career roster: allies, hire market, deploy flags, digest refunds."""

from __future__ import annotations

import json
import random
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

ROSTER_TUNING_PATH = DATA_DIR / "roster_tuning.json"
MAX_ALLIES_DEFAULT = 4
MAX_DEPLOY_DEFAULT = 2
DIGEST_REFUND_DEFAULT = 0.7


@attrs.define
class AllyRecord:
    ally_id: str
    name: str
    species_id: str
    tier: str  # scrub | learner | finished
    hire_cost: int
    training_spent: int = 0
    deployed: bool = False
    backstory: str = ""
    max_hp: int = 12
    accuracy: float = 1.0
    evade: float = 1.0
    ac: int = 0
    min_damage: int = 1
    max_damage: int = 2
    learn_rate: float = 0.0
    # Match order: attack | defend
    order: str = "attack"
    injuries: list[dict[str, Any]] = attrs.field(factory=list)
    # Beast companions may be vore-capable; anthro default False (PC never vores)
    vore_capable: bool = False

    def investment(self) -> int:
        return int(self.hire_cost) + int(self.training_spent)

    def digest_refund(self, fraction: float = DIGEST_REFUND_DEFAULT) -> int:
        return max(0, int(round(self.investment() * fraction)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ally_id": self.ally_id,
            "name": self.name,
            "species_id": self.species_id,
            "tier": self.tier,
            "hire_cost": self.hire_cost,
            "training_spent": self.training_spent,
            "deployed": self.deployed,
            "backstory": self.backstory,
            "max_hp": self.max_hp,
            "accuracy": self.accuracy,
            "evade": self.evade,
            "ac": self.ac,
            "min_damage": self.min_damage,
            "max_damage": self.max_damage,
            "learn_rate": self.learn_rate,
            "order": self.order,
            "injuries": list(self.injuries),
            "vore_capable": self.vore_capable,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AllyRecord:
        return cls(
            ally_id=str(data.get("ally_id") or uuid.uuid4().hex[:8]),
            name=str(data.get("name") or "Fighter"),
            species_id=str(data.get("species_id") or "kobold"),
            tier=str(data.get("tier") or "scrub"),
            hire_cost=int(data.get("hire_cost", 0)),
            training_spent=int(data.get("training_spent", 0)),
            deployed=bool(data.get("deployed", False)),
            backstory=str(data.get("backstory") or ""),
            max_hp=int(data.get("max_hp", 12)),
            accuracy=float(data.get("accuracy", 1.0)),
            evade=float(data.get("evade", 1.0)),
            ac=int(data.get("ac", 0)),
            min_damage=int(data.get("min_damage", 1)),
            max_damage=int(data.get("max_damage", 2)),
            learn_rate=float(data.get("learn_rate", 0.0)),
            order=str(data.get("order") or "attack"),
            injuries=list(data.get("injuries") or []),
            vore_capable=bool(data.get("vore_capable", False)),
        )


@attrs.define(frozen=True)
class RosterTuning:
    max_allies: int = MAX_ALLIES_DEFAULT
    max_deployed_allies: int = MAX_DEPLOY_DEFAULT
    digest_refund_fraction: float = DIGEST_REFUND_DEFAULT
    free_starter_picks: int = 2
    market_offer_count: int = 5
    tiers: dict[str, dict[str, Any]] = attrs.field(factory=dict)
    species_pool: tuple[str, ...] = ("kobold", "rat", "wolf")
    # Species that may be hired as vore-capable beast companions (not anthros)
    beast_vore_species: tuple[str, ...] = ("wolf", "rat")
    jobs: tuple[str, ...] = ()
    locations: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


@lru_cache(maxsize=1)
def load_roster_tuning(path: Path | None = None) -> RosterTuning:
    p = path if path is not None else ROSTER_TUNING_PATH
    if not p.is_file():
        return RosterTuning()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return RosterTuning()
    tiers = raw.get("tiers") if isinstance(raw.get("tiers"), dict) else {}
    return RosterTuning(
        max_allies=int(raw.get("max_allies", MAX_ALLIES_DEFAULT)),
        max_deployed_allies=int(raw.get("max_deployed_allies", MAX_DEPLOY_DEFAULT)),
        digest_refund_fraction=float(
            raw.get("digest_refund_fraction", DIGEST_REFUND_DEFAULT)
        ),
        free_starter_picks=int(raw.get("free_starter_picks", 2)),
        market_offer_count=int(raw.get("market_offer_count", 5)),
        tiers=dict(tiers),
        species_pool=tuple(raw.get("species_pool") or ("kobold", "rat", "wolf")),
        beast_vore_species=tuple(
            raw.get("beast_vore_species") or ("wolf", "rat")
        ),
        jobs=tuple(raw.get("jobs") or ()),
        locations=tuple(raw.get("locations") or ()),
        reasons=tuple(raw.get("reasons") or ()),
    )


def reset_roster_tuning_cache() -> None:
    load_roster_tuning.cache_clear()


_FIRST_NAMES = (
    "Brask",
    "Sela",
    "Torvik",
    "Mira",
    "Jorn",
    "Kessa",
    "Venn",
    "Oda",
    "Rilk",
    "Tamsin",
    "Gorr",
    "Nyla",
)


def _rand_range(rng: random.Random, lo: int, hi: int) -> int:
    if hi < lo:
        lo, hi = hi, lo
    return rng.randint(lo, hi)


def _rand_float(rng: random.Random, lo: float, hi: float) -> float:
    if hi < lo:
        lo, hi = hi, lo
    return rng.uniform(lo, hi)


def generate_ally(
    rng: random.Random,
    *,
    tier: str | None = None,
    free: bool = False,
    tuning: RosterTuning | None = None,
) -> AllyRecord:
    """Procedural hire offer within a tier archetype."""
    cfg = tuning if tuning is not None else load_roster_tuning()
    tier_id = tier or rng.choice(list(cfg.tiers.keys()) or ["scrub"])
    t = cfg.tiers.get(tier_id) or cfg.tiers.get("scrub") or {}
    species = rng.choice(cfg.species_pool) if cfg.species_pool else "kobold"
    name = rng.choice(_FIRST_NAMES)
    job = rng.choice(cfg.jobs) if cfg.jobs else "wanderer"
    loc = rng.choice(cfg.locations) if cfg.locations else "the pits"
    reason = rng.choice(cfg.reasons) if cfg.reasons else "fate"
    backstory = (
        f"Originally a {job} from {loc} who became a gladiator because of {reason}."
    )
    hp_lo, hp_hi = (t.get("hp") or [10, 16])[:2]
    acc_lo, acc_hi = (t.get("accuracy") or [0.8, 1.2])[:2]
    ev_lo, ev_hi = (t.get("evade") or [0.8, 1.2])[:2]
    dmg_lo, dmg_hi = (t.get("damage") or [1, 2])[:2]
    hire_lo = int(t.get("hire_min", 10))
    hire_hi = int(t.get("hire_max", 40))
    hire = 0 if free else _rand_range(rng, hire_lo, hire_hi)
    max_hp = _rand_range(rng, int(hp_lo), int(hp_hi))
    min_d = int(dmg_lo)
    max_d = max(min_d, int(dmg_hi))
    vore_ok = species in cfg.beast_vore_species
    return AllyRecord(
        ally_id=uuid.uuid4().hex[:10],
        name=name,
        species_id=species,
        tier=tier_id,
        hire_cost=hire,
        training_spent=0,
        deployed=False,
        backstory=backstory,
        max_hp=max_hp,
        accuracy=_rand_float(rng, float(acc_lo), float(acc_hi)),
        evade=_rand_float(rng, float(ev_lo), float(ev_hi)),
        ac=0 if tier_id == "scrub" else rng.randint(0, 1),
        min_damage=min_d,
        max_damage=max_d,
        learn_rate=float(t.get("learn_rate", 0.0)),
        order="attack",
        vore_capable=vore_ok,
    )


def generate_market(
    rng: random.Random,
    *,
    count: int | None = None,
    free: bool = False,
    tuning: RosterTuning | None = None,
) -> list[AllyRecord]:
    cfg = tuning if tuning is not None else load_roster_tuning()
    n = count if count is not None else cfg.market_offer_count
    tiers = list(cfg.tiers.keys()) or ["scrub", "learner", "finished"]
    offers: list[AllyRecord] = []
    for i in range(n):
        # Bias: include each tier if possible
        tier = tiers[i % len(tiers)]
        offers.append(generate_ally(rng, tier=tier, free=free, tuning=cfg))
    return offers


def roster_from_career_dicts(raw: list[dict[str, Any]]) -> list[AllyRecord]:
    return [AllyRecord.from_dict(d) for d in raw if isinstance(d, dict)]


def roster_to_career_dicts(allies: list[AllyRecord]) -> list[dict[str, Any]]:
    return [a.to_dict() for a in allies]


def deployed_allies(allies: list[AllyRecord], *, max_deploy: int) -> list[AllyRecord]:
    chosen = [a for a in allies if a.deployed]
    return chosen[:max_deploy]


def count_deployed(allies: list[AllyRecord]) -> int:
    return sum(1 for a in allies if a.deployed)


def try_hire(
    allies: list[AllyRecord],
    offer: AllyRecord,
    *,
    gold: int,
    free: bool = False,
    max_allies: int | None = None,
) -> tuple[list[AllyRecord], int, str | None]:
    """Return (new_roster, new_gold, error)."""
    cfg = load_roster_tuning()
    cap = max_allies if max_allies is not None else cfg.max_allies
    if len(allies) >= cap:
        return allies, gold, f"Roster full ({cap} allies max)."
    cost = 0 if free else offer.hire_cost
    if gold < cost:
        return allies, gold, f"Need {cost} gold (have {gold})."
    hired = AllyRecord(
        **{**offer.to_dict(), "hire_cost": cost, "deployed": False}
    )
    # Ensure unique id
    hired.ally_id = uuid.uuid4().hex[:10]
    return [*allies, hired], gold - cost, None


def remove_ally_digest(
    allies: list[AllyRecord],
    ally_id: str,
    *,
    gold: int,
    refund_fraction: float | None = None,
) -> tuple[list[AllyRecord], int, int]:
    """Remove ally; refund fraction of investment. Returns (roster, gold, refund)."""
    cfg = load_roster_tuning()
    frac = (
        refund_fraction
        if refund_fraction is not None
        else cfg.digest_refund_fraction
    )
    remaining: list[AllyRecord] = []
    refund = 0
    for a in allies:
        if a.ally_id == ally_id:
            refund = a.digest_refund(frac)
        else:
            remaining.append(a)
    return remaining, gold + refund, refund
