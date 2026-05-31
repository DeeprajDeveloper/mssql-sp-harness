"""Optional step-by-step run log for analyze / generate."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

ProgressCallback = Callable[[str], None]
LogCallback = Callable[[str, str], None]


def truncate_for_log(text: str, *, max_len: int = 120) -> str:
    """Single-line preview for log files."""
    one_line = " ".join(text.split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 3] + "..."


def emit_log(callback: LogCallback | None, function: str, message: str) -> None:
    if callback is not None:
        callback(function, message)


class RunLogger:
    """Append timestamped messages to a log file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._opened = False

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write(self, level: str, function: str, message: str) -> None:
        line = f"[{self._timestamp()}] [{function}] [{level}] {message}\n"
        with self.path.open("a", encoding="utf-8") as handle:
            if not self._opened:
                handle.write(
                    f"[{self._timestamp()}] [RunLogger] [INFO ] "
                    "sql-sp-harness run log started\n"
                )
                self._opened = True
            handle.write(line)

    def info(self, function: str, message: str) -> None:
        self._write("INFO ", function, message)

    def detail(self, function: str, message: str) -> None:
        self._write("DEBUG", function, message)

    def warning(self, function: str, message: str) -> None:
        self._write("WARN ", function, message)

    def error(self, function: str, message: str) -> None:
        self._write("ERROR", function, message)

    def as_info_callback(self) -> LogCallback:
        """Milestone messages (transform / analyze steps)."""

        def _cb(function: str, message: str) -> None:
            self.info(function, message)

        return _cb

    def as_detail_callback(self) -> LogCallback:
        """Per-line / per-edit messages for verbose ``--log`` output."""

        def _cb(function: str, message: str) -> None:
            self.detail(function, message)

        return _cb

    def as_progress_callback(self) -> ProgressCallback:
        """Backward-compatible: logs to ``transform_sql`` at INFO level."""

        info = self.as_info_callback()

        def _cb(message: str) -> None:
            info("transform_sql", message)

        return _cb

    def close(self, *, command: str, success: bool = True) -> None:
        status = "completed" if success else "finished with errors"
        self.info("close", f"{command} {status}")


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
