"""Utilities for scanning and cleaning timestamped files in stata-mcp folders."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..config import Config

logger = logging.getLogger(__name__)

_TIMESTAMP_PATTERN = re.compile(r"^(\d{14})(\d{6})?")


def _parse_timestamp_from_stem(stem: str) -> datetime | None:
    """Parse a leading timestamp from file stem."""
    match = _TIMESTAMP_PATTERN.match(stem)
    if match is None:
        return None

    main_part = match.group(1)
    microseconds = match.group(2)
    if microseconds:
        stamp = f"{main_part}{microseconds}"
        fmt = "%Y%m%d%H%M%S%f"
    else:
        stamp = main_part
        fmt = "%Y%m%d%H%M%S"

    try:
        return datetime.strptime(stamp, fmt)
    except ValueError:
        return None


def scan_old_files(dirs: list[Path], max_age_days: int, now: datetime | None = None) -> list[Path]:
    """Scan non-recursively and return files older than max_age_days."""
    current_time = now or datetime.now()
    effective_days = max(max_age_days, 0)
    cutoff = current_time - timedelta(days=effective_days)
    results: list[Path] = []

    for directory in dirs:
        if not directory.exists() or not directory.is_dir():
            continue
        for path in directory.iterdir():
            if not path.is_file():
                continue
            file_timestamp = _parse_timestamp_from_stem(path.stem)
            if file_timestamp is None:
                continue
            if file_timestamp <= cutoff:
                results.append(path)

    return results


def clean_log_files(
    max_age_days: int,
    dry_run: bool = False,
    config: Config | None = None,
    candidate_files: list[Path] | None = None,
) -> dict[str, Any]:
    """Clean old timestamped files from log/do/tmp folders."""
    if config is None:
        from ..config import Config

        cfg = Config()
    else:
        cfg = config
    target_dirs = [
        cfg.STATA_MCP_FOLDER.LOG,
        cfg.STATA_MCP_FOLDER.DO,
        cfg.STATA_MCP_FOLDER.TMP,
    ]
    candidates = (
        candidate_files
        if candidate_files is not None
        else scan_old_files(target_dirs, max_age_days=max_age_days)
    )
    candidate_size = 0
    for path in candidates:
        try:
            candidate_size += path.stat().st_size
        except OSError:
            continue

    if dry_run:
        return {
            "deleted_count": 0,
            "skipped_count": len(candidates),
            "failed_count": 0,
            "freed_bytes": candidate_size,
            "errors": [],
            "dry_run": True,
        }

    deleted_count = 0
    skipped_count = 0
    failed_count = 0
    freed_bytes = 0
    errors: list[dict[str, str]] = []

    for file_path in candidates:
        if not file_path.exists():
            skipped_count += 1
            continue
        try:
            size = file_path.stat().st_size
        except OSError:
            size = 0
        try:
            file_path.unlink()
            deleted_count += 1
            freed_bytes += size
            logger.info("Deleted old file: %s", file_path)
        except OSError as error:
            failed_count += 1
            errors.append({"path": str(file_path), "error": str(error)})
            logger.warning("Failed to delete old file %s: %s", file_path, error)

    return {
        "deleted_count": deleted_count,
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "freed_bytes": freed_bytes,
        "errors": errors,
        "dry_run": False,
    }
