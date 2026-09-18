"""Privacy-safe stack snapshots for slow MCP tool calls."""

from __future__ import annotations

import os
import sys
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path

from .checkpoints import write_checkpoint


class SlowCallWatchdog:
    """Record all Python thread locations when a target tool runs long."""

    def __init__(
        self,
        *,
        tool: str,
        run_id: str,
        trace_id: str | None = None,
        span_id: str | None = None,
        process_id: int | None = None,
        delays: tuple[float, ...] = (30.0, 120.0),
    ) -> None:
        self.tool = tool
        self.run_id = run_id
        self.trace_id = trace_id
        self.span_id = span_id
        self.process_id = os.getpid() if process_id is None else process_id
        self.delays = delays
        self._timers: list[threading.Timer] = []
        self._finished = threading.Event()

    def start(self) -> None:
        """Schedule non-blocking slow-call snapshots."""
        try:
            for delay in self.delays:
                timer = threading.Timer(delay, self._write_snapshot, args=(delay,))
                timer.daemon = True
                timer.start()
                self._timers.append(timer)
        except Exception:
            self.cancel()

    def cancel(self) -> None:
        """Cancel snapshots that have not fired."""
        self._finished.set()
        for timer in self._timers:
            timer.cancel()
        self._timers.clear()

    def _write_snapshot(self, delay: float) -> None:
        if self._finished.is_set():
            return

        thread_names = {
            thread.ident: thread.name
            for thread in threading.enumerate()
            if thread.ident is not None
        }
        threads = []
        for thread_id, frame in sorted(sys._current_frames().items()):
            extracted_stack = traceback.extract_stack(frame, limit=16)
            stack = " > ".join(
                f"{Path(item.filename).name}:{item.lineno}:{item.name}"
                for item in extracted_stack
            )
            threads.append(
                {
                    "thread_id": thread_id,
                    "thread_name": thread_names.get(thread_id, "unknown"),
                    "stack": stack,
                }
            )

        if self._finished.is_set():
            return
        payload = {
            "schema_version": 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "slow",
            "step": f"{self.tool}.watchdog",
            "tool": self.tool,
            "run_id": self.run_id,
            "process_id": self.process_id,
            "delay_seconds": delay,
            "threads": threads,
        }
        if self.trace_id is not None:
            payload["trace_id"] = self.trace_id
        if self.span_id is not None:
            payload["span_id"] = self.span_id
        write_checkpoint(payload)
