"""Save/load snapshot layer (PR1: in-memory round-trip; PR2+: file store)."""

from src.save.schema import SAVE_FORMAT_VERSION, build_save_envelope
from src.save.snapshot import apply_run_snapshot, build_run_snapshot
from src.save.migrate import SaveMigrationError, migrate_run
from src.save.coordinator import (
    AUTOSAVE_TIME_INTERVAL_SECONDS,
    AUTOSAVE_TURN_INTERVAL,
    SaveCoordinator,
)
from src.save.store import (
    SaveNotFoundError,
    SaveStore,
    SaveStoreError,
    SaveValidationError,
    SaveWriteError,
    compute_payload_sha256,
)

__all__ = [
    "AUTOSAVE_TIME_INTERVAL_SECONDS",
    "AUTOSAVE_TURN_INTERVAL",
    "SAVE_FORMAT_VERSION",
    "SaveCoordinator",
    "SaveMigrationError",
    "SaveNotFoundError",
    "SaveStore",
    "SaveStoreError",
    "SaveValidationError",
    "SaveWriteError",
    "apply_run_snapshot",
    "build_run_snapshot",
    "build_save_envelope",
    "compute_payload_sha256",
    "migrate_run",
]