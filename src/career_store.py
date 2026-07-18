"""JSON career save (Gladiavore meta-progression between matches)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.career import CareerState
from src.user_data import SAVES_DIR

CAREER_FILENAME = "career.json"
CAREER_TMP = "career.tmp.json"


class CareerStoreError(Exception):
    """Career save I/O or validation failure."""


class CareerNotFoundError(CareerStoreError):
    """No career file on disk."""


class CareerStore:
    """Single-slot career file under the saves directory."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory if directory is not None else SAVES_DIR

    @property
    def path(self) -> Path:
        return self.directory / CAREER_FILENAME

    def probe(self) -> bool:
        return self.path.is_file() and self.path.stat().st_size > 0

    def save(self, career: CareerState) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = career.to_dict()
        text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        tmp = self.directory / CAREER_TMP
        tmp.write_text(text + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    def load(self) -> CareerState:
        if not self.probe():
            raise CareerNotFoundError("no career save")
        try:
            raw: Any = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CareerStoreError("invalid career json") from exc
        if not isinstance(raw, dict):
            raise CareerStoreError("career root must be an object")
        return CareerState.from_dict(raw)

    def delete(self) -> None:
        for name in (CAREER_FILENAME, CAREER_TMP):
            path = self.directory / name
            if path.is_file():
                path.unlink()
