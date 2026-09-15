"""Match card catalog + round offers + economy (JSON-driven)."""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

import attrs

from src.constants import DATA_DIR

MATCH_CARDS_PATH = DATA_DIR / "match_cards.json"


@attrs.define(frozen=True)
class MatchEconomy:
    win_gold_base: int = 40
    green_loss_gold_base: int = 15
    red_loss_gold_base: int = 5
    win_renown_red: int = 2
    win_renown_green: int = 1
    loss_renown: int = 0
    surrender_min_world_aut: float = 2.5
    surrender_base_fraction: float = 0.3
    surrender_aut_bonus_per_aut: float = 0.04
    surrender_fraction_max: float = 0.8


@attrs.define(frozen=True)
class CardDef:
    card_id: str
    title: str
    kind: str  # green | red
    payout_mult: float
    max_allies: int
    min_round: int
    max_round: int
    enemies: tuple[tuple[str, int], ...]  # (entity_id, count)


@attrs.define(frozen=True)
class MatchCardsConfig:
    offer_count: int = 3
    green_rounds: tuple[int, ...] = (1, 3, 5, 7, 10, 14)
    green_rounds_easier_extra: tuple[int, ...] = (2, 4, 6, 8, 12)
    economy: MatchEconomy = attrs.field(factory=MatchEconomy)
    cards: tuple[CardDef, ...] = ()
    by_id: dict[str, CardDef] = attrs.field(factory=dict)


@lru_cache(maxsize=1)
def load_match_cards_config(path: Path | None = None) -> MatchCardsConfig:
    p = path if path is not None else MATCH_CARDS_PATH
    if not p.is_file():
        return _fallback_config()
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return _fallback_config()
    return _parse(raw)


def reset_match_cards_cache() -> None:
    load_match_cards_config.cache_clear()


def _fallback_config() -> MatchCardsConfig:
    cards = (
        CardDef(
            "r1_rats",
            "3 dire rats (exhibition pit)",
            "red",
            1.0,
            2,
            1,
            99,
            (("rat", 3),),
        ),
        CardDef(
            "r1_kobolds",
            "Kobold knife squad",
            "red",
            1.1,
            2,
            1,
            99,
            (("kobold", 3),),
        ),
        CardDef(
            "r1_green_spar",
            "Sparring exhibition (nonlethal)",
            "green",
            0.45,
            2,
            1,
            99,
            (("rat", 1),),
        ),
    )
    return MatchCardsConfig(
        cards=cards,
        by_id={c.card_id: c for c in cards},
    )


def _parse(raw: dict[str, Any]) -> MatchCardsConfig:
    econ_raw = raw.get("economy") if isinstance(raw.get("economy"), dict) else {}
    economy = MatchEconomy(
        win_gold_base=int(econ_raw.get("win_gold_base", 40)),
        green_loss_gold_base=int(econ_raw.get("green_loss_gold_base", 15)),
        red_loss_gold_base=int(econ_raw.get("red_loss_gold_base", 5)),
        win_renown_red=int(econ_raw.get("win_renown_red", 2)),
        win_renown_green=int(econ_raw.get("win_renown_green", 1)),
        loss_renown=int(econ_raw.get("loss_renown", 0)),
        surrender_min_world_aut=float(econ_raw.get("surrender_min_world_aut", 2.5)),
        surrender_base_fraction=float(econ_raw.get("surrender_base_fraction", 0.3)),
        surrender_aut_bonus_per_aut=float(
            econ_raw.get("surrender_aut_bonus_per_aut", 0.04)
        ),
        surrender_fraction_max=float(econ_raw.get("surrender_fraction_max", 0.8)),
    )
    cards_list: list[CardDef] = []
    for item in raw.get("cards") or []:
        if not isinstance(item, dict):
            continue
        enemies: list[tuple[str, int]] = []
        for e in item.get("enemies") or []:
            if not isinstance(e, dict):
                continue
            eid = str(e.get("entity_id") or "rat")
            cnt = max(1, int(e.get("count", 1)))
            enemies.append((eid, cnt))
        if not enemies:
            enemies = [("rat", 1)]
        cid = str(item.get("id") or item.get("card_id") or "")
        if not cid:
            continue
        cards_list.append(
            CardDef(
                card_id=cid,
                title=str(item.get("title") or cid),
                kind=str(item.get("kind") or "red").lower(),
                payout_mult=float(item.get("payout_mult", 1.0)),
                max_allies=int(item.get("max_allies", 2)),
                min_round=int(item.get("min_round", 1)),
                max_round=int(item.get("max_round", 99)),
                enemies=tuple(enemies),
            )
        )
    if not cards_list:
        return _fallback_config()
    by_id = {c.card_id: c for c in cards_list}
    return MatchCardsConfig(
        offer_count=max(1, int(raw.get("offer_count", 3))),
        green_rounds=tuple(int(x) for x in (raw.get("green_rounds") or [1, 3, 5])),
        green_rounds_easier_extra=tuple(
            int(x) for x in (raw.get("green_rounds_easier_extra") or [])
        ),
        economy=economy,
        cards=tuple(cards_list),
        by_id=by_id,
    )


def is_solo_eligible_card(card: CardDef | Any) -> bool:
    """True if the card is a pure 1v1 duel (one enemy id, count 1)."""
    enemies = getattr(card, "enemies", None) or ()
    if len(enemies) != 1:
        return False
    _eid, count = enemies[0]
    return int(count) == 1


def green_allowed_for_round(
    round_index: int,
    *,
    difficulty_id: str = "normal",
    cfg: MatchCardsConfig | None = None,
) -> bool:
    c = cfg if cfg is not None else load_match_cards_config()
    rounds = set(c.green_rounds)
    # Easier (or any tier with extra_green_rounds) gets more mercy bouts
    try:
        from src.difficulties import resolve_difficulty

        diff = resolve_difficulty(difficulty_id)
        if diff.extra_green_rounds or difficulty_id == "easier":
            rounds.update(c.green_rounds_easier_extra)
    except Exception:
        if difficulty_id == "easier":
            rounds.update(c.green_rounds_easier_extra)
    return int(round_index) in rounds


def eligible_card_defs(
    round_index: int,
    *,
    difficulty_id: str = "normal",
    cfg: MatchCardsConfig | None = None,
    solo_only: bool = False,
) -> list[CardDef]:
    c = cfg if cfg is not None else load_match_cards_config()
    allow_green = green_allowed_for_round(
        round_index, difficulty_id=difficulty_id, cfg=c
    )
    out: list[CardDef] = []
    for card in c.cards:
        if solo_only and not is_solo_eligible_card(card):
            continue
        if round_index < card.min_round or round_index > card.max_round:
            continue
        if card.kind == "green" and not allow_green:
            continue
        out.append(card)
    if not out:
        # Always offer something — prefer same style constraints
        fallback = list(c.cards)
        if solo_only:
            fallback = [x for x in fallback if is_solo_eligible_card(x)]
        out = [x for x in fallback if x.kind == "red"] or fallback
    return out


def pick_match_offers(
    round_index: int,
    *,
    difficulty_id: str = "normal",
    rng: random.Random | None = None,
    cfg: MatchCardsConfig | None = None,
    solo_only: bool = False,
) -> tuple[Any, ...]:
    """Return up to offer_count MatchCard instances for the hub."""
    from src.downtime_hub import MatchCard

    c = cfg if cfg is not None else load_match_cards_config()
    r = rng if rng is not None else random.Random()
    pool = eligible_card_defs(
        round_index,
        difficulty_id=difficulty_id,
        cfg=c,
        solo_only=solo_only,
    )
    n = min(c.offer_count, len(pool))
    if n <= 0:
        return ()
    chosen = r.sample(pool, n) if len(pool) >= n else list(pool)
    cards = tuple(_def_to_match_card(d, force_solo=solo_only) for d in chosen)
    return cards


def _def_to_match_card(d: CardDef, *, force_solo: bool = False) -> Any:
    from src.downtime_hub import MatchCard

    max_allies = 0 if force_solo else d.max_allies
    return MatchCard(
        card_id=d.card_id,
        title=d.title,
        kind=d.kind if d.kind in ("green", "red") else "red",
        payout_mult=d.payout_mult,
        max_allies=max_allies,
        enemies=d.enemies,
    )


def enemies_for_card(card: Any) -> tuple[tuple[str, int], ...]:
    """Resolve spawn list from card field or catalog by id."""
    enemies = getattr(card, "enemies", None) or ()
    if enemies:
        return tuple(enemies)
    cfg = load_match_cards_config()
    d = cfg.by_id.get(getattr(card, "card_id", ""))
    if d is not None:
        return d.enemies
    return (("rat", 1),)


def compute_win_payout(
    card: Any,
    economy: MatchEconomy | None = None,
    *,
    difficulty_payout_mult: float = 1.0,
) -> tuple[int, int]:
    e = economy if economy is not None else load_match_cards_config().economy
    gold = max(
        1,
        int(
            round(
                e.win_gold_base
                * float(card.payout_mult)
                * float(difficulty_payout_mult)
            )
        ),
    )
    renown = e.win_renown_red if card.kind == "red" else e.win_renown_green
    return gold, renown


def compute_loss_payout(
    card: Any,
    economy: MatchEconomy | None = None,
    *,
    difficulty_payout_mult: float = 1.0,
) -> tuple[int, int]:
    e = economy if economy is not None else load_match_cards_config().economy
    mult = float(card.payout_mult) * float(difficulty_payout_mult)
    if card.kind == "green":
        gold = max(1, int(round(e.green_loss_gold_base * mult)))
    else:
        gold = max(0, int(round(e.red_loss_gold_base * mult)))
    return gold, e.loss_renown


def compute_surrender_payout(
    card: Any,
    *,
    world_aut: float,
    economy: MatchEconomy | None = None,
    difficulty_payout_mult: float = 1.0,
) -> tuple[int, int, float]:
    """Green mid-match surrender: scaled appearance fee. Returns gold, renown, fraction used."""
    e = economy if economy is not None else load_match_cards_config().economy
    base, renown = compute_loss_payout(
        card, e, difficulty_payout_mult=difficulty_payout_mult
    )
    frac = e.surrender_base_fraction + max(0.0, world_aut) * e.surrender_aut_bonus_per_aut
    frac = min(e.surrender_fraction_max, max(0.0, frac))
    gold = max(1, int(round(base * frac)))
    return gold, renown, frac
