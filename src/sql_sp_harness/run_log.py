"""Optional step-by-step run log for analyze / generate."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

ProgressCallback = Callable[[str], None]


class RunLogger:
    """Append timestamped messages to a log file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._opened = False

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write(self, level: str, message: str) -> None:
        line = f"[{self._timestamp()}] [{level}] {message}\n"
        with self.path.open("a", encoding="utf-8") as handle:
            if not self._opened:
                handle.write(
                    f"[{self._timestamp()}] [INFO  ] sql-sp-harness run log started\n"
                )
                self._opened = True
            handle.write(line)

    def info(self, message: str) -> None:
        self._write("INFO  ", message)

    def detail(self, message: str) -> None:
        self._write("DETAIL", message)

    def warning(self, message: str) -> None:
        self._write("WARN  ", message)

    def error(self, message: str) -> None:
        self._write("ERROR ", message)

    def as_progress_callback(self) -> ProgressCallback:
        """Compatible with transform ``on_progress`` callbacks."""

        def _cb(message: str) -> None:
            self.info(message)

        return _cb

    def close(self, *, command: str, success: bool = True) -> None:
        status = "completed" if success else "finished with errors"
        self.info(f"{command} {status}")


def resolve_log_path(
    input_path: Path,
    *,
    log: bool,
    log_file: Path | None,
) -> Path | None:
    """Choose log file path from ``--log`` and/or ``--log-file``."""
    if log_file is not None:
        return log_file
    if log and str(input_path) != "-":
        return input_path.with_name(f"{input_path.stem}.log")
    return None


def combine_progress(*callbacks: ProgressCallback | None) -> ProgressCallback | None:
    """Invoke multiple progress handlers for the same message."""
    active = [cb for cb in callbacks if cb is not None]
    if not active:
        return None

    def _combined(message: str) -> None:
        for cb in active:
            cb(message)

    return _combined
