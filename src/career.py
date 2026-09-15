"""Gladiavore career run state (between-match meta)."""

from __future__ import annotations

from typing import Any

import attrs

from src.injuries import InjuryInstance, injuries_from_dicts, injuries_to_dicts
from src.roster import (
    AllyRecord,
    load_roster_tuning,
    roster_from_career_dicts,
    roster_to_career_dicts,
)

CAREER_FORMAT_VERSION = 1
STARTING_GOLD = 100

# Campaign styles: solo = 1v1 duels (active product); company = team/multi (on ice).
CAMPAIGN_STYLE_SOLO = "solo"
CAMPAIGN_STYLE_COMPANY = "company"


@attrs.define
class CareerState:
    """In-memory career for downtime hub and (later) match settlement."""

    player_name: str = "Anonymous"
    gold: int = STARTING_GOLD
    renown: int = 0
    round_index: int = 1
    difficulty_id: str = "normal"
    roster: list[dict[str, Any]] = attrs.field(factory=list)
    max_deployed_allies: int = 2
    # Set false until free starter picks complete (company only).
    starter_picks_done: bool = False
    # PC injuries persist across matches (stamina does not).
    player_injuries: list[dict[str, Any]] = attrs.field(factory=list)
    # Last patron objective result (hub flavor); empty if none yet.
    last_patron_result: str = ""
    # Background stub (long-term goals later).
    background_id: str = ""
    # solo | company — pre-alpha default solo
    campaign_style: str = CAMPAIGN_STYLE_SOLO

    def is_solo(self) -> bool:
        return str(self.campaign_style or CAMPAIGN_STYLE_SOLO) == CAMPAIGN_STYLE_SOLO

    def is_company(self) -> bool:
        return not self.is_solo()

    def allies(self) -> list[AllyRecord]:
        return roster_from_career_dicts(self.roster)

    def set_allies(self, allies: list[AllyRecord]) -> None:
        self.roster = roster_to_career_dicts(allies)

    def get_player_injuries(self) -> list[InjuryInstance]:
        return injuries_from_dicts(self.player_injuries)

    def set_player_injuries(self, injuries: list[InjuryInstance]) -> None:
        self.player_injuries = injuries_to_dicts(injuries)

    def to_dict(self) -> dict[str, Any]:
        return {
            "career_format_version": CAREER_FORMAT_VERSION,
            "player_name": self.player_name,
            "gold": int(self.gold),
            "renown": int(self.renown),
            "round_index": int(self.round_index),
            "difficulty_id": str(self.difficulty_id),
            "roster": list(self.roster),
            "max_deployed_allies": int(self.max_deployed_allies),
            "starter_picks_done": bool(self.starter_picks_done),
            "player_injuries": list(self.player_injuries),
            "last_patron_result": str(self.last_patron_result or ""),
            "background_id": str(self.background_id or ""),
            "campaign_style": str(self.campaign_style or CAMPAIGN_STYLE_SOLO),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CareerState:
        version = data.get("career_format_version", 1)
        if version != CAREER_FORMAT_VERSION:
            pass
        roster = list(data.get("roster") or [])
        style = str(data.get("campaign_style") or CAMPAIGN_STYLE_SOLO).lower()
        if style not in (CAMPAIGN_STYLE_SOLO, CAMPAIGN_STYLE_COMPANY):
            style = CAMPAIGN_STYLE_SOLO
        starter_done = data.get("starter_picks_done")
        if starter_done is None:
            if style == CAMPAIGN_STYLE_SOLO:
                starter_done = True
            else:
                starter_done = len(roster) > 0
        tuning = load_roster_tuning()
        max_dep = int(data.get("max_deployed_allies", tuning.max_deployed_allies))
        if style == CAMPAIGN_STYLE_SOLO:
            max_dep = 0
            roster = []
            starter_done = True
        return cls(
            player_name=str(data.get("player_name") or "Anonymous"),
            gold=int(data.get("gold", STARTING_GOLD)),
            renown=int(data.get("renown", 0)),
            round_index=max(1, int(data.get("round_index", 1))),
            difficulty_id=str(data.get("difficulty_id") or "normal"),
            roster=roster,
            max_deployed_allies=max_dep,
            starter_picks_done=bool(starter_done),
            player_injuries=list(data.get("player_injuries") or []),
            last_patron_result=str(data.get("last_patron_result") or ""),
            background_id=str(data.get("background_id") or ""),
            campaign_style=style,
        )


def new_career(
    *,
    player_name: str,
    difficulty_id: str = "normal",
    campaign_style: str = CAMPAIGN_STYLE_SOLO,
) -> CareerState:
    """Fresh career after name entry.

    Solo (default): no allies, starter gate skipped.
    Company (on ice): starter ally picks still required.
    """
    tuning = load_roster_tuning()
    style = (
        campaign_style
        if campaign_style in (CAMPAIGN_STYLE_SOLO, CAMPAIGN_STYLE_COMPANY)
        else CAMPAIGN_STYLE_SOLO
    )
    if style == CAMPAIGN_STYLE_SOLO:
        return CareerState(
            player_name=player_name,
            gold=STARTING_GOLD,
            renown=0,
            round_index=1,
            difficulty_id=difficulty_id,
            roster=[],
            max_deployed_allies=0,
            starter_picks_done=True,
            campaign_style=CAMPAIGN_STYLE_SOLO,
        )
    return CareerState(
        player_name=player_name,
        gold=STARTING_GOLD,
        renown=0,
        round_index=1,
        difficulty_id=difficulty_id,
        max_deployed_allies=tuning.max_deployed_allies,
        starter_picks_done=False,
        campaign_style=CAMPAIGN_STYLE_COMPANY,
    )
