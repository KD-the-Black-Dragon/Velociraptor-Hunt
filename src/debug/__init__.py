"""Player-facing diagnostics: session logs, crash reports (see submodules)."""

from src.debug.context import CrashContext, build_crash_context
from src.debug.crash_report import (
    format_crash_report,
    install_crash_handler,
    register_app,
    register_ui,
    unregister_ui,
    write_crash_report,
)
from src.debug.modal_snapshot import active_modal_label
from src.debug.paths import LOGS_DIR, crash_log_path, session_log_path, startup_error_log_path
from src.debug.startup_error import (
    STARTUP_JSON_ERROR_HEADING,
    append_startup_error_log,
    format_startup_error_display,
    report_startup_json_error,
)
from src.debug.session_log import (
    SessionLogCoordinator,
    reset_quit_milestone_state,
    session_log,
    should_log_quit_milestone,
    skip_quit_milestone,
)
from src.debug.version_info import GAME_VERSION, collect_platform_info, get_game_version

__all__ = [
    "CrashContext",
    "GAME_VERSION",
    "LOGS_DIR",
    "STARTUP_JSON_ERROR_HEADING",
    "SessionLogCoordinator",
    "active_modal_label",
    "append_startup_error_log",
    "build_crash_context",
    "crash_log_path",
    "collect_platform_info",
    "format_crash_report",
    "format_startup_error_display",
    "install_crash_handler",
    "register_app",
    "register_ui",
    "report_startup_json_error",
    "get_game_version",
    "reset_quit_milestone_state",
    "session_log",
    "session_log_path",
    "startup_error_log_path",
    "should_log_quit_milestone",
    "skip_quit_milestone",
    "unregister_ui",
    "write_crash_report",
]