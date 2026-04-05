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
    except Exception:
        pass

    try:
        install_root = Path(dist.locate_file(""))
        install_root_text = str(install_root).lower()
        if "cellar" in install_root_text and "homebrew" in install_root_text:
            return InstallMethod.HOMEBREW
        if "site-packages" in install_root_text or "dist-packages" in install_root_text:
            return InstallMethod.PIP
    except Exception:
        pass

    return InstallMethod.UNKNOWN


def get_current_version() -> str:
    """Return currently installed version."""
    return version("stata-mcp")


def get_latest_version() -> Optional[str]:
    """Fetch latest version from PyPI."""
    try:
        with urlopen(PYPI_API_URL, timeout=10) as response:
            payload = json.loads(response.read())
        return payload["info"]["version"]
    except Exception:
        return None


def build_update_command(method: InstallMethod) -> Optional[list[str]]:
    """Build the update command for a specific install method."""
    if method == InstallMethod.UV_TOOL:
        return ["uv", "tool", "upgrade", "stata-mcp"]
    if method == InstallMethod.PIP:
        return [sys.executable, "-m", "pip", "install", "--upgrade", "stata-mcp"]
    if method == InstallMethod.HOMEBREW:
        return ["brew", "upgrade", "stata-mcp"]
    if method == InstallMethod.UNKNOWN:
        return [sys.executable, "-m", "pip", "install", "--upgrade", "stata-mcp"]
    return None


def _run_update_command(command: list[str]) -> bool:
    """Run update command and return True on success."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
        if result.returncode == 0:
            return True
        logging.error("Update command failed: %s", result.stderr.strip())
        return False
    except FileNotFoundError:
        logging.error("Update command not found: %s", command[0])
        return False
    except subprocess.TimeoutExpired:
        logging.error("Update command timed out")
        return False


def execute_update(method: Optional[InstallMethod] = None) -> tuple[bool, str]:
    """Execute update and return (success, message)."""
    resolved_method = method or detect_install_method()
    current = get_current_version()
    latest = get_latest_version()

    if latest is None:
        return False, "Failed to fetch latest version from PyPI"

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

    command = build_update_command(resolved_method)
    if command is None:
        return False, f"No supported update command for install method: {resolved_method.value}"

    message_lines = [
        f"stata-mcp v{current} → v{latest}",
        f"Detected: {resolved_method.value}",
        f"Running: {' '.join(command)}",
    ]

    if _run_update_command(command):
        message_lines.append("✅ Updated successfully")
        return True, "\n".join(message_lines)

    message_lines.append("❌ Update failed")
    return False, "\n".join(message_lines)
