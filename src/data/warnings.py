from __future__ import annotations


class LoadWarnings:
    """Collect load warnings; each key is emitted at most once per load session."""

    def __init__(self) -> None:
        self._seen: set[str] = set()
        self._messages: list[str] = []

    def warn_once(self, key: str, message: str) -> None:
        if key in self._seen:
            return
        self._seen.add(key)
        self._messages.append(message)

    def warn_unknown_trait(self, trait: str, entity_id: str) -> None:
        self.warn_once(
            f"trait:unknown:{trait}",
            f"Unknown trait '{trait}' on '{entity_id}' — ignored",
        )

    def warn_reserved_trait(self, trait: str, entity_id: str) -> None:
        self.warn_once(
            f"trait:reserved:{trait}",
            f"Trait '{trait}' on '{entity_id}' — ignored (not implemented)",
        )

    def warn_unknown_ability(self, ability: str, entity_id: str) -> None:
        self.warn_once(
            f"ability:unknown:{ability}",
            f"Unknown ability '{ability}' on '{entity_id}' — ignored",
        )

    def warn_unimplemented_ability(self, ability: str, entity_id: str) -> None:
        self.warn_once(
            f"ability:unimplemented:{ability}",
            f"Ability '{ability}' on '{entity_id}' — documented but not implemented",
        )

    def warn_ranged_stats_defaulted(self, entity_id: str) -> None:
        self.warn_once(
            f"ranged:default:{entity_id}",
            f"Entity '{entity_id}' has SmiteN/RangeN but omitted ranged_* stats — using melee values",
        )

    @property
    def messages(self) -> tuple[str, ...]:
        return tuple(self._messages)