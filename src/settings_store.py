from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import attrs

from src.constants import (
    DEFAULT_VORE_CONTENT_PREFS,
    VORE_NARRATIVE_TYPES_V1,
    VoreContentPreferences,
)
from src.ui.window_state import WindowPreferences, window_from_dict, window_to_dict
from src.user_data import SETTINGS_PATH


def _validate_enabled_codes(codes: list[str]) -> frozenset[str]:
    valid = frozenset(VORE_NARRATIVE_TYPES_V1)
    filtered = {code for code in codes if code in valid}
    if not filtered:
        return DEFAULT_VORE_CONTENT_PREFS.enabled
    return frozenset(filtered)


def _default_ui_preset() -> str:
    from src.ui.layout import UILayoutLoadError

    try:
        from src.mods.pipeline import load_ui_layout_document_layered

        raw, _issues = load_ui_layout_document_layered(report=False)
    except (OSError, json.JSONDecodeError, UILayoutLoadError, ValueError):
        return "standard"
    preset = raw.get("default_preset", "standard")
    return preset if isinstance(preset, str) and preset.strip() else "standard"


def _validate_ui_preset(value: str | None) -> str:
    from src.ui.layout import UILayoutLoadError, load_ui_layout

    default = _default_ui_preset()
    if not value or not isinstance(value, str) or not value.strip():
        return default
    try:
        load_ui_layout(value.strip())
    except UILayoutLoadError:
        return default
    return value.strip()


def _load_layout_for_window_validation(ui_preset: str):
    from src.ui.layout import load_ui_layout

    return load_ui_layout(ui_preset)


def _default_difficulty_id() -> str:
    from src.difficulties import load_difficulties

    return load_difficulties().default_id


def _validate_difficulty_id(value: str | None) -> str:
    from src.difficulties import load_difficulties

    cfg = load_difficulties()
    if value and value in cfg.by_id:
        return value
    return cfg.default_id


@attrs.define
class SettingsStore:
    """Persistent user settings (vore content prefs in v1)."""

    vore_content: VoreContentPreferences = DEFAULT_VORE_CONTENT_PREFS
    ui_preset: str = attrs.field(factory=_default_ui_preset)
    difficulty_id: str = attrs.field(factory=_default_difficulty_id)
    window: WindowPreferences = attrs.field(factory=WindowPreferences)
    window_saved_on_disk: bool = False
    tutorial_prompt_answered: bool = False
    vore_prefs_onboarding_complete: bool = False
    path: Path = SETTINGS_PATH

    @classmethod
    def load(cls, path: Path = SETTINGS_PATH) -> SettingsStore:
        """Load settings from disk, or return defaults if missing or invalid."""
        if not path.is_file():
            return cls(path=path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls(path=path)
        store = cls.from_dict(raw)
        return attrs.evolve(store, path=path)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SettingsStore:
        vore_raw = data.get("vore_content", {})
        enabled_raw = vore_raw.get("enabled", list(VORE_NARRATIVE_TYPES_V1))
        if not isinstance(enabled_raw, list):
            enabled_raw = list(VORE_NARRATIVE_TYPES_V1)
        enabled = _validate_enabled_codes([str(code) for code in enabled_raw])
        ui_preset = _validate_ui_preset(
            str(data["ui_preset"]) if "ui_preset" in data else None
        )
        difficulty_raw = data.get("difficulty_id")
        difficulty_id = _validate_difficulty_id(
            str(difficulty_raw) if difficulty_raw is not None else None
        )
        window_raw = data.get("window")
        window_saved = isinstance(window_raw, dict)
        if window_saved:
            layout = _load_layout_for_window_validation(ui_preset)
            window = window_from_dict(window_raw, layout)
        else:
            window = WindowPreferences()
        return cls(
            vore_content=VoreContentPreferences(enabled=enabled),
            ui_preset=ui_preset,
            difficulty_id=difficulty_id,
            window=window,
            window_saved_on_disk=window_saved,
            tutorial_prompt_answered=bool(data.get("tutorial_prompt_answered", False)),
            vore_prefs_onboarding_complete=bool(
                data.get("vore_prefs_onboarding_complete", False),
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "vore_content": {
                "enabled": sorted(self.vore_content.enabled),
            },
            "ui_preset": self.ui_preset,
            "difficulty_id": self.difficulty_id,
            "window": window_to_dict(self.window),
            "tutorial_prompt_answered": self.tutorial_prompt_answered,
            "vore_prefs_onboarding_complete": self.vore_prefs_onboarding_complete,
        }

    def save(self, path: Path | None = None) -> None:
        """Write settings to disk."""
        target = path or self.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

    def set_vore_content(self, prefs: VoreContentPreferences) -> None:
        """Update vore prefs and persist immediately."""
        self.vore_content = prefs
        self.save()

    def set_ui_preset(self, preset: str) -> None:
        """Update UI layout preset and persist immediately."""
        validated = _validate_ui_preset(preset)
        if validated == self.ui_preset:
            return
        self.ui_preset = validated
        self.save()

    def set_difficulty_id(self, difficulty_id: str) -> None:
        """Update Options difficulty (next new game) and persist immediately."""
        validated = _validate_difficulty_id(difficulty_id)
        if validated == self.difficulty_id:
            return
        self.difficulty_id = validated
        self.save()

    def mark_tutorial_prompt_answered(self) -> None:
        """Record first-run tutorial prompt answered (Yes or No)."""
        if self.tutorial_prompt_answered:
            return
        self.tutorial_prompt_answered = True
        self.save()

    def mark_vore_prefs_onboarding_complete(self) -> None:
        """Record first-run vore preference screen confirmed."""
        if self.vore_prefs_onboarding_complete:
            return
        self.vore_prefs_onboarding_complete = True
        self.save()