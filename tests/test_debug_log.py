"""PR0: debug stdout env gate."""

from __future__ import annotations

from src.debug_log import DEBUG_STDOUT_ENV, debug_print, debug_stdout_enabled


def test_debug_stdout_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv(DEBUG_STDOUT_ENV, raising=False)
    assert not debug_stdout_enabled()


def test_debug_stdout_enabled_values(monkeypatch) -> None:
    for value in ("1", "true", "TRUE", " yes ", "on"):
        monkeypatch.setenv(DEBUG_STDOUT_ENV, value)
        assert debug_stdout_enabled()


def test_debug_print_suppressed_without_env(monkeypatch, capsys) -> None:
    monkeypatch.delenv(DEBUG_STDOUT_ENV, raising=False)
    debug_print("hidden debug line", flush=True)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_debug_print_emits_when_env_set(monkeypatch, capsys) -> None:
    monkeypatch.setenv(DEBUG_STDOUT_ENV, "1")
    debug_print("visible debug line", flush=True)
    captured = capsys.readouterr()
    assert "visible debug line" in captured.out