"""Debug hook to trigger crash reporting on demand (F6 during PLAY)."""


class ForceCrashError(RuntimeError):
    """Raised by the F6 debug hotkey to exercise crash reporting."""


def trigger_force_crash() -> None:
    """Raise an unhandled exception for manual crash-report testing."""
    raise ForceCrashError("F6 debug force-crash")