"""Logging configuration for Odoo API application"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings

DEBUG_QUALNAME = "odoo-api"


class SimpleLogger:
    """Simple file-based logger that doesn't rely on Python's logging module

    Features lazy initialization: filesystem operations are deferred until the
    first log write. If the filesystem is read-only (e.g. Vercel serverless),
    the logger gracefully falls back to stdout-only logging.
    """

    def __init__(self, log_file: str = "logs/odoo_api.log", max_size: int = 10485760):
        self.log_file_path = Path(log_file)
        self.max_size = max_size
        self.backup_count = 5
        self._log_file = None  # Resolved at first write; None = stdout-only
        self._initialized = False

    def _ensure_log_dir(self):
        """Lazily create the log directory on first write.

        If the filesystem is read-only (e.g. Vercel), sets _log_file to None
        so all subsequent writes go to stdout only.
        """
        if self._initialized:
            return
        self._initialized = True

        try:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            self._log_file = self.log_file_path
        except OSError:
            # Read-only filesystem (e.g. Vercel serverless) — fall back to stdout
            self._log_file = None

    def _rotate_if_needed(self):
        """Rotate log file if it exceeds max size"""
        if self._log_file is None:
            return
        try:
            if (
                self._log_file.exists()
                and self._log_file.stat().st_size > self.max_size
            ):
                # Rotate existing backups
                for i in range(self.backup_count - 1, 0, -1):
                    old_file = (
                        self._log_file.parent
                        / f"{self._log_file.stem}.{i}{self._log_file.suffix}"
                    )
                    new_file = (
                        self._log_file.parent
                        / f"{self._log_file.stem}.{i+1}{self._log_file.suffix}"
                    )
                    if old_file.exists():
                        old_file.rename(new_file)

                # Rotate current log file
                backup_file = (
                    self._log_file.parent
                    / f"{self._log_file.stem}.1{self._log_file.suffix}"
                )
                if self._log_file.exists():
                    self._log_file.rename(backup_file)
        except OSError:
            pass  # Silently degrade on read-only filesystem

    def _write_log(self, level: str, message: str):
        """Write a log message to file and/or stdout"""
        self._ensure_log_dir()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {level} - {message}\n"

        # Always print to stdout (works everywhere, including Vercel)
        print(log_entry.strip())

        # Write to file if filesystem is writable
        if self._log_file is not None:
            try:
                self._rotate_if_needed()
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry)
            except OSError:
                pass  # Silently degrade on read-only filesystem

    def debug(self, message: str):
        """Log debug message"""
        if settings.DEBUG:
            self._write_log("DEBUG", message)

    def info(self, message: str):
        """Log info message"""
        self._write_log("INFO", message)

    def warning(self, message: str):
        """Log warning message"""
        self._write_log("WARNING", message)

    def error(self, message: str):
        """Log error message"""
        self._write_log("ERROR", message)


def setup_logging(log_level: Optional[str] = None, log_file: Optional[str] = None):
    """
    Setup logging configuration for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file, defaults to 'logs/odoo_api.log'
    """
    # This function is kept for compatibility but doesn't do much
    # The SimpleLogger handles its own configuration
    pass


def get_logger(name: str = "odoo-api") -> SimpleLogger:
    """
    Get a logger instance with the specified name

    Args:
        name: Logger name

    Returns:
        SimpleLogger instance
    """
    return SimpleLogger()


def tail_logs(log_file: str = "logs/odoo_api.log", lines: int = 100) -> list[str]:
    """
    Tail the last N lines from a log file

    Args:
        log_file: Path to log file
        lines: Number of lines to return

    Returns:
        List of log lines
    """
    log_path = Path(log_file)

    if not log_path.exists():
        return [f"Log file not found: {log_file}"]

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            # Read all lines and return the last N
            all_lines = f.readlines()
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
    except Exception as e:
        return [f"Error reading log file: {str(e)}"]


def get_log_files() -> list[str]:
    """
    Get list of available log files

    Returns:
        List of log file paths
    """
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return []

    log_files = []
    for file_path in logs_dir.glob("*.log"):
        log_files.append(str(file_path))

    return sorted(log_files)


# Global logger instance — created at import time but does NOT touch the
# filesystem until the first log message is actually written.
logger = get_logger()
