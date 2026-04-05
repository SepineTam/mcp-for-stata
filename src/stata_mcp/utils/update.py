"""Package update detection and execution utilities."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from enum import Enum
from importlib.metadata import PackageNotFoundError, distribution, version
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


class InstallMethod(str, Enum):
    """Supported installation methods for the package."""

    PIP = "pip"
    UV_TOOL = "uv-tool"
    UVX = "uvx"
    EDITABLE = "editable"
    HOMEBREW = "homebrew"
    UNKNOWN = "unknown"


PYPI_API_URL = "https://pypi.org/pypi/stata-mcp/json"


def get_uv_tool_dir() -> Path:
    """Return uv tool directory by environment variable or platform default."""
    if "UV_TOOL_DIR" in os.environ:
        return Path(os.environ["UV_TOOL_DIR"])

    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "uv" / "tools"

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / "uv" / "tools"


def _path_is_relative_to(path: Path, root: Path) -> bool:
    """Return True if path is under root."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_uvx_runtime(python_path: Path) -> bool:
    """Best-effort uvx runtime detection based on runtime path and env vars."""
    executable_text = str(python_path).lower()

    if any(key.startswith("UV_INTERNAL__") for key in os.environ):
        return True

    if "uvx" in executable_text and "cache" in executable_text:
        return True

    if ".cache" in executable_text and "uv" in executable_text and "archive-v0" in executable_text:
        return True

    return False


def detect_install_method() -> InstallMethod:
    """Detect how stata-mcp was installed."""
    try:
        dist = distribution("stata-mcp")
    except PackageNotFoundError:
        logging.warning("Package metadata for stata-mcp was not found while detecting install method.")
        return InstallMethod.UNKNOWN

    python_path = Path(sys.executable).resolve()
    uv_tool_dir = get_uv_tool_dir().resolve()
    if _path_is_relative_to(python_path, uv_tool_dir):
        return InstallMethod.UV_TOOL

    if _is_uvx_runtime(python_path):
        return InstallMethod.UVX

    try:
        direct_url_raw = dist.read_text("direct_url.json")
        if direct_url_raw:
            direct_url = json.loads(direct_url_raw)
            if direct_url.get("dir_info", {}).get("editable", False):
                return InstallMethod.EDITABLE
    except json.JSONDecodeError as error:
        logging.warning("Failed to parse direct_url.json while detecting editable install: %s", error)
    except PermissionError as error:
        logging.warning("Permission denied while reading direct_url.json: %s", error)
    except Exception as error:
        logging.debug("Ignored direct_url.json read failure: %s", error)

    try:
        install_root = Path(dist.locate_file(""))
        install_root_text = str(install_root).lower()
        if "cellar" in install_root_text and "homebrew" in install_root_text:
            return InstallMethod.HOMEBREW
        if "site-packages" in install_root_text or "dist-packages" in install_root_text:
            return InstallMethod.PIP
    except PermissionError as error:
        logging.warning("Permission denied while resolving package install root: %s", error)
    except Exception as error:
        logging.debug("Ignored install root resolution failure: %s", error)

    return InstallMethod.UNKNOWN


def get_current_version() -> str:
    """Return currently installed version."""
    return version("stata-mcp")


def get_latest_version() -> tuple[Optional[str], Optional[str]]:
    """Fetch latest version from PyPI with a user-facing error message."""
    try:
        with urlopen(PYPI_API_URL, timeout=10) as response:
            payload = json.loads(response.read())
        latest = payload["info"]["version"]
        if not isinstance(latest, str) or not latest:
            return None, "PyPI response did not include a valid version string."
        return latest, None
    except HTTPError as error:
        return None, f"PyPI request failed with HTTP {error.code}."
    except URLError as error:
        return None, f"Failed to reach PyPI: {error.reason}."
    except TimeoutError:
        return None, "Timed out while requesting latest version from PyPI."
    except json.JSONDecodeError as error:
        return None, f"Failed to parse PyPI response JSON: {error}."
    except KeyError as error:
        return None, f"PyPI response format changed, missing key: {error}."
    except Exception as error:
        return None, f"Unexpected error while checking latest version: {error}."


def build_update_command(method: InstallMethod) -> Optional[list[str]]:
    """Build the update command for a specific install method."""
    if method == InstallMethod.UV_TOOL:
        return ["uv", "tool", "upgrade", "stata-mcp"]
    if method == InstallMethod.PIP:
        return [sys.executable, "-m", "pip", "install", "--upgrade", "stata-mcp"]
    if method == InstallMethod.HOMEBREW:
        return ["brew", "upgrade", "stata-mcp"]
    return None


def _run_update_command(command: list[str]) -> tuple[bool, str]:
    """Run update command and return success plus a detail message."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
        if result.returncode == 0:
            detail = result.stdout.strip() or "Command completed successfully."
            return True, detail

        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        detail = stderr or stdout or f"Command exited with status {result.returncode}."
        logging.error("Update command failed: %s", detail)
        return False, detail
    except FileNotFoundError:
        detail = f"Command not found: {command[0]}"
        logging.error(detail)
        return False, detail
    except subprocess.TimeoutExpired:
        detail = "Update command timed out."
        logging.error(detail)
        return False, detail
    except OSError as error:
        detail = f"Failed to execute update command due to OS error: {error}"
        logging.error(detail)
        return False, detail


def execute_update(method: Optional[InstallMethod] = None) -> tuple[bool, str]:
    """Execute update and return (success, message)."""
    resolved_method = method or detect_install_method()
    try:
        current = get_current_version()
    except PackageNotFoundError:
        return False, "stata-mcp is not installed in this Python environment."
    except Exception as error:
        return False, f"Failed to determine current installed version: {error}"

    latest, latest_error = get_latest_version()

    if latest is None:
        return False, latest_error or "Failed to fetch latest version from PyPI."

    if current == latest:
        return True, f"stata-mcp v{current} (already latest)"

    if resolved_method == InstallMethod.UVX:
        return True, (
            "⚠️  You are running via uvx, which always pulls the latest version.\n"
            "   No update needed — just re-run your command."
        )

    if resolved_method == InstallMethod.EDITABLE:
        return False, (
            "⚠️  Running in editable/development mode.\n"
            "   Use git pull to update, or pip install -e . to reinstall."
        )

    if resolved_method == InstallMethod.UNKNOWN and method is None:
        return False, (
            "⚠️  Could not determine installation method automatically.\n"
            "   Refusing to run fallback update to avoid unexpected double installation.\n"
            "   Re-run with --method pip or --method uv-tool."
        )

    command = build_update_command(resolved_method)
    if command is None:
        return False, f"No supported update command for install method: {resolved_method.value}"

    message_lines = [
        f"stata-mcp v{current} → v{latest}",
        f"Detected: {resolved_method.value}",
        f"Running: {' '.join(command)}",
    ]

    success, detail = _run_update_command(command)
    if success:
        message_lines.append("✅ Updated successfully")
        message_lines.append(f"Details: {detail}")
        return True, "\n".join(message_lines)

    message_lines.append(f"❌ Update failed: {detail}")
    return False, "\n".join(message_lines)
