"""Shared helpers for privacy-safe diagnostic logging."""

from __future__ import annotations

import hashlib
import json
import logging
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path
from typing import Any

DIAGNOSTIC_BUILD_ID = "windows-get-data-info-debug-v1"
DIAGNOSTIC_SCHEMA_VERSION = 1


def new_request_id() -> str:
    """Return a short identifier used to correlate one tool invocation."""
    return uuid.uuid4().hex[:12]


def source_reference(source: object) -> str:
    """Return a stable one-way reference without logging a source path or URL."""
    source_bytes = str(source).encode("utf-8", errors="surrogatepass")
    return hashlib.sha256(source_bytes).hexdigest()[:12]


def elapsed_ms(started_at: float) -> int:
    """Return elapsed monotonic time in whole milliseconds."""
    return round((time.perf_counter() - started_at) * 1000)


def safe_stack(error: BaseException, *, limit: int = 16) -> str:
    """Return traceback locations without absolute paths, source text, or locals."""
    extracted_stack = traceback.extract_tb(error.__traceback__, limit=limit)
    return " > ".join(
        f"{Path(item.filename).name}:{item.lineno}:{item.name}"
        for item in extracted_stack
    )


def utf8_size(value: str) -> int:
    """Return a diagnostic UTF-8 size without rejecting isolated surrogates."""
    return len(value.encode("utf-8", errors="backslashreplace"))


def process_log_path(log_path: str | Path, *, pid: int) -> Path:
    """Return a per-process log path so Windows processes do not rotate one file."""
    path = Path(log_path)
    return path.with_name(f"{path.stem}.{pid}{path.suffix}")


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    request_id: str,
    **fields: Any,
) -> None:
    """Write a stable key-value event with JSON-escaped field values."""
    serialized_fields = " ".join(
        f"{key}={_serialize_log_value(value)}" for key, value in sorted(fields.items())
    )
    suffix = f" {serialized_fields}" if serialized_fields else ""
    logger.log(level, "event=%s request_id=%s%s", event, request_id, suffix)


def _serialize_log_value(value: Any) -> str:
    """Serialize one diagnostic value without allowing log-line injection."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=True)


class DiagnosticWatchdog:
    """Log privacy-safe stack locations when a synchronous operation runs long."""

    def __init__(
        self,
        logger: logging.Logger,
        request_id: str,
        *,
        delays: tuple[float, ...] = (30.0, 120.0),
    ) -> None:
        self._logger = logger
        self._request_id = request_id
        self._delays = delays
        self._target_thread_id = threading.get_ident()
        self._timers: list[threading.Timer] = []
        self._finished = threading.Event()

    def start(self) -> None:
        """Schedule stack snapshots without allowing diagnostics to fail the tool."""
        try:
            for delay in self._delays:
                timer = threading.Timer(delay, self._log_snapshot, args=(delay,))
                timer.daemon = True
                timer.start()
                self._timers.append(timer)
        except Exception as error:
            self.cancel()
            log_event(
                self._logger,
                logging.WARNING,
                "get_data_info.watchdog.start_failed",
                self._request_id,
                error_type=type(error).__name__,
            )

    def cancel(self) -> None:
        """Cancel snapshots that have not fired yet."""
        self._finished.set()
        for timer in self._timers:
            timer.cancel()
        self._timers.clear()

    def _log_snapshot(self, delay: float) -> None:
        if self._finished.is_set():
            return
        frame = sys._current_frames().get(self._target_thread_id)
        if frame is None:
            if self._finished.is_set():
                return
            log_event(
                self._logger,
                logging.WARNING,
                "get_data_info.watchdog.stack_unavailable",
                self._request_id,
                delay_seconds=delay,
                target_thread_id=self._target_thread_id,
            )
            return

        extracted_stack = traceback.extract_stack(frame, limit=16)
        stack_locations = " > ".join(
            f"{Path(item.filename).name}:{item.lineno}:{item.name}"
            for item in extracted_stack
        )
        if self._finished.is_set():
            return
        log_event(
            self._logger,
            logging.WARNING,
            "get_data_info.watchdog.stack_snapshot",
            self._request_id,
            delay_seconds=delay,
            stack=stack_locations,
            target_thread_id=self._target_thread_id,
        )
