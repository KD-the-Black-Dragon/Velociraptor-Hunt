"""Rotating autosave file store with integrity validation."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from src.save.schema import SAVE_FORMAT_VERSION, RunSnapshot, build_save_envelope
from src.user_data import SAVES_DIR

PRIMARY_NAME = "autosave.json"
BAK1_NAME = "autosave.bak1.json"
BAK2_NAME = "autosave.bak2.json"
BAK3_NAME = "autosave.bak3.json"
TMP_NAME = "autosave.tmp"

SAVE_DIR = SAVES_DIR
LOAD_CHAIN = (PRIMARY_NAME, BAK1_NAME, BAK2_NAME, BAK3_NAME)
ALL_SLOT_FILES = (*LOAD_CHAIN, TMP_NAME)


class SaveStoreError(Exception):
    """Base error for save file operations."""


class SaveNotFoundError(SaveStoreError):
    """No valid save exists in the slot chain."""


class SaveValidationError(SaveStoreError):
    """A save file failed parse or integrity checks."""


class SaveWriteError(SaveStoreError):
    """Autosave could not be written (permissions, disk full, file locked, etc.)."""


def canonical_run_json(run: RunSnapshot) -> str:
    """Deterministic JSON for hashing the run payload."""
    return json.dumps(run, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_payload_sha256(run: RunSnapshot) -> str:
    return hashlib.sha256(canonical_run_json(run).encode("utf-8")).hexdigest()


def serialize_envelope(envelope: dict[str, Any]) -> bytes:
    text = json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return text.encode("utf-8")


def parse_envelope_bytes(data: bytes) -> dict[str, Any]:
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SaveValidationError("invalid save json") from exc
    if not isinstance(document, dict):
        raise SaveValidationError("save document must be an object")
    return document


def validate_envelope(document: dict[str, Any]) -> RunSnapshot:
    version = document.get("save_format_version")
    if version != SAVE_FORMAT_VERSION:
        raise SaveValidationError(f"unsupported save_format_version: {version!r}")

    run = document.get("run")
    if not isinstance(run, dict):
        raise SaveValidationError("missing run payload")

    expected = str(document.get("payload_sha256", ""))
    actual = compute_payload_sha256(run)
    if expected != actual:
        raise SaveValidationError("payload_sha256 mismatch")

    return run


class SaveStore:
    """Single-slot autosave chain under the user data ``saves/`` dir (or a custom directory)."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory if directory is not None else SAVE_DIR

    def primary_path(self) -> Path:
        return self.directory / PRIMARY_NAME

    def path_for(self, name: str) -> Path:
        return self.directory / name

    def probe(self) -> bool:
        """Return True when any file in the load chain is valid."""
        try:
            self.load_best()
        except SaveNotFoundError:
            return False
        return True

    def load_best(self) -> RunSnapshot:
        """Load the newest valid save (primary, then backups)."""
        last_error: SaveValidationError | None = None
        for name in LOAD_CHAIN:
            path = self.path_for(name)
            if not path.is_file():
                continue
            try:
                return self._load_file(path)
            except SaveValidationError as exc:
                last_error = exc
                continue
        if last_error is not None:
            raise SaveNotFoundError("no valid save in slot chain") from last_error
        raise SaveNotFoundError("no save files found")

    def save_run(
        self,
        run: RunSnapshot,
        *,
        saved_at_unix: int | None = None,
    ) -> None:
        """Serialize, validate, and rotate a new autosave into the slot chain."""
        payload_sha256 = compute_payload_sha256(run)
        envelope = build_save_envelope(
            run,
            saved_at_unix=saved_at_unix,
            payload_sha256=payload_sha256,
        )
        data = serialize_envelope(envelope)
        validate_envelope(parse_envelope_bytes(data))
        self._rotate(data)

    def delete_all(self) -> None:
        """Remove all autosave slot files (best-effort)."""
        for name in ALL_SLOT_FILES:
            path = self.path_for(name)
            try:
                path.unlink(missing_ok=True)
            except OSError:
                continue

    def _load_file(self, path: Path) -> RunSnapshot:
        return validate_envelope(parse_envelope_bytes(path.read_bytes()))

    def _rotate(self, data: bytes) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path_for(TMP_NAME)
        primary = self.path_for(PRIMARY_NAME)
        bak1 = self.path_for(BAK1_NAME)
        bak2 = self.path_for(BAK2_NAME)
        bak3 = self.path_for(BAK3_NAME)

        try:
            with tmp_path.open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())

            if bak3.is_file():
                bak3.unlink()
            if bak2.is_file():
                os.replace(bak2, bak3)
            if bak1.is_file():
                os.replace(bak1, bak2)
            if primary.is_file():
                os.replace(primary, bak1)
            os.replace(tmp_path, primary)
        except OSError as exc:
            raise SaveWriteError("could not write autosave file") from exc