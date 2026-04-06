#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Diagnostic checks for stata-mcp health status."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from importlib.metadata import PackageNotFoundError, version as pkg_version
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


class CheckStatus(Enum):
    """Status values for a doctor check."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class CheckResult:
    """Single check result."""

    name: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    hint: str | None = None


@dataclass
class DoctorReport:
    """Aggregated report from all checks."""

    version: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return any(check.status == CheckStatus.FAIL for check in self.checks)

    @property
    def failure_count(self) -> int:
        return sum(1 for check in self.checks if check.status == CheckStatus.FAIL)

    @property
    def warning_count(self) -> int:
        return sum(1 for check in self.checks if check.status == CheckStatus.WARN)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to a serializable dictionary."""
        return {
            "version": self.version,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                    "hint": check.hint,
                }
                for check in self.checks
            ],
            "summary": {
                "total": len(self.checks),
                "passed": sum(1 for c in self.checks if c.status == CheckStatus.PASS),
                "failed": self.failure_count,
                "warnings": self.warning_count,
                "skipped": sum(1 for c in self.checks if c.status == CheckStatus.SKIP),
            },
        }

    def to_json(self) -> str:
        """Convert report to pretty JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def check_os() -> CheckResult:
    """Check operating system compatibility."""
    system = platform.system()
    os_map = {"Darwin": "macOS", "Linux": "Linux", "Windows": "Windows"}
    friendly_name = os_map.get(system, system)
    is_supported = system in os_map

    return CheckResult(
        name="os",
        status=CheckStatus.PASS if is_supported else CheckStatus.FAIL,
        message=f"{friendly_name} ({system} {platform.release()}, {platform.machine()})",
        details={
            "system": system,
            "release": platform.release(),
            "machine": platform.machine(),
        },
        hint=None if is_supported else "This operating system is not officially supported.",
    )


def check_python() -> CheckResult:
    """Check Python version compatibility."""
    info = sys.version_info
    version_text = f"{info.major}.{info.minor}.{info.micro}"
    is_supported = info.major == 3 and info.minor >= 11

    return CheckResult(
        name="python",
        status=CheckStatus.PASS if is_supported else CheckStatus.FAIL,
        message=f"{version_text} ({sys.executable})",
        details={
            "version": version_text,
            "executable": sys.executable,
        },
        hint=None if is_supported else "Python 3.11+ is required.",
    )


def check_uv() -> CheckResult:
    """Check whether uv is available."""
    uv_path = shutil.which("uv")
    if uv_path is None:
        return CheckResult(
            name="uv",
            status=CheckStatus.WARN,
            message="not found",
            details={"path": None, "version": None},
            hint="Install uv for faster installation: https://docs.astral.sh/uv/",
        )

    uv_version = "unknown"
    try:
        command_result = subprocess.run(
            [uv_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        candidate = command_result.stdout.strip() or command_result.stderr.strip()
        if candidate:
            uv_version = candidate
        if command_result.returncode != 0:
            return CheckResult(
                name="uv",
                status=CheckStatus.WARN,
                message=f"found but version detection failed ({uv_path})",
                details={"path": uv_path, "version": uv_version},
                hint="Reinstall uv or verify that `uv --version` works in your shell.",
            )
    except (OSError, subprocess.TimeoutExpired):
        return CheckResult(
            name="uv",
            status=CheckStatus.WARN,
            message=f"found but version detection failed ({uv_path})",
            details={"path": uv_path, "version": uv_version},
            hint="Reinstall uv or verify that `uv --version` works in your shell.",
        )

    return CheckResult(
        name="uv",
        status=CheckStatus.PASS,
        message=f"{uv_version} ({uv_path})",
        details={"path": uv_path, "version": uv_version},
    )


def check_dependencies() -> CheckResult:
    """Check required and optional dependencies."""
    required = ["mcp", "pydantic", "tomli_w"]
    optional = ["pandas", "numpy", "psutil", "pexpect"]
    installed: dict[str, bool] = {}
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for package in required:
        try:
            __import__(package)
            installed[package] = True
        except ImportError:
            installed[package] = False
            missing_required.append(package)

    for package in optional:
        try:
            __import__(package)
            installed[package] = True
        except ImportError:
            installed[package] = False
            missing_optional.append(package)

    if missing_required:
        return CheckResult(
            name="dependencies",
            status=CheckStatus.FAIL,
            message=f"missing required: {', '.join(missing_required)}",
            details={
                "installed": installed,
                "missing_required": missing_required,
                "missing_optional": missing_optional,
            },
            hint="Reinstall stata-mcp to restore required dependencies.",
        )

    if missing_optional:
        return CheckResult(
            name="dependencies",
            status=CheckStatus.WARN,
            message=f"optional missing: {', '.join(missing_optional)}",
            details={
                "installed": installed,
                "missing_required": [],
                "missing_optional": missing_optional,
            },
            hint="Optional packages are needed for some features.",
        )

    return CheckResult(
        name="dependencies",
        status=CheckStatus.PASS,
        message="all required packages available",
        details={
            "installed": installed,
            "missing_required": [],
            "missing_optional": [],
        },
    )


def _resolve_stata_cli(config: Any) -> tuple[str | None, str | None]:
    """Resolve Stata CLI path and source."""
    env_cli = os.getenv("STATA_CLI")
    if env_cli:
        env_path = Path(env_cli).expanduser()
        if env_path.exists():
            return str(env_path), "env"

    config_cli = config.config.get("STATA", {}).get("STATA_CLI")
    if config_cli:
        config_path = Path(config_cli).expanduser()
        if config_path.exists():
            return str(config_path), "config"

    try:
        from ..stata import StataFinder

        finder_cli = StataFinder(None).STATA_CLI
        if finder_cli:
            finder_path = Path(finder_cli).expanduser()
            if finder_path.exists():
                return str(finder_path), "finder"
    except (OSError, PermissionError, RuntimeError, ValueError):
        return None, None

    return None, None


def check_stata_cli(config: Any) -> CheckResult:
    """Check whether Stata CLI can be located."""
    stata_cli, source = _resolve_stata_cli(config)
    if stata_cli is None:
        return CheckResult(
            name="stata_cli",
            status=CheckStatus.FAIL,
            message="not found",
            details={"path": None, "source": None},
            hint="Set STATA_CLI or run `stata-mcp config cli set`.",
        )

    source_suffix = "auto-detected" if source == "finder" else f"from {source}"
    return CheckResult(
        name="stata_cli",
        status=CheckStatus.PASS,
        message=f"{stata_cli} ({source_suffix})",
        details={"path": stata_cli, "source": source},
    )


def check_stata_execution(config: Any, stata_cli_path: str | None) -> CheckResult:
    """Check whether Stata executable can run commands."""
    if not stata_cli_path:
        return CheckResult(
            name="stata_execution",
            status=CheckStatus.SKIP,
            message="skipped (no Stata CLI found)",
            details={},
        )

    commands = 'display "Stata-MCP Doctor Test"\nexit, STATA\n'
    start_time = time.monotonic()

    try:
        if config.IS_UNIX:
            process = subprocess.Popen(
                [stata_cli_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
            try:
                process.communicate(input=commands, timeout=15)
                return_code = process.returncode
            finally:
                if process.poll() is None:
                    try:
                        process.terminate()
                    except OSError:
                        pass

                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:
                            process.kill()
                        except OSError:
                            pass
                        try:
                            process.wait(timeout=5)
                        except (subprocess.TimeoutExpired, OSError):
                            pass
        else:
            temp_do_file = config.STATA_MCP_DIRECTORY / "doctor_test.do"
            try:
                temp_do_file.write_text(commands, encoding="utf-8")
            except (OSError, PermissionError) as error:
                return CheckResult(
                    name="stata_execution",
                    status=CheckStatus.FAIL,
                    message=f"temp file write failed: {error}",
                    details={"temp_do_file": str(temp_do_file)},
                    hint="Set STATA_MCP__CWD to a writable directory.",
                )
            try:
                win_result = subprocess.run(
                    f'"{stata_cli_path}" /e do "{temp_do_file}"',
                    shell=True,
                    timeout=15,
                    check=False,
                )
            finally:
                if temp_do_file.exists():
                    temp_do_file.unlink()
            return_code = win_result.returncode
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="stata_execution",
            status=CheckStatus.FAIL,
            message="timeout (>15s)",
            details={},
            hint="Stata execution timed out. Check license dialogs or blocked startup prompts.",
        )
    except OSError as error:
        return CheckResult(
            name="stata_execution",
            status=CheckStatus.FAIL,
            message=f"execution error: {error}",
            details={},
            hint="Verify Stata installation and execution permissions.",
        )

    elapsed = round(time.monotonic() - start_time, 1)
    is_ok = return_code == 0

    return CheckResult(
        name="stata_execution",
        status=CheckStatus.PASS if is_ok else CheckStatus.FAIL,
        message=f"{'OK' if is_ok else 'FAILED'} ({elapsed}s)",
        details={"elapsed_s": elapsed, "returncode": return_code},
        hint=None if is_ok else "Stata was found but command execution failed.",
    )


def check_config(config: Any) -> CheckResult:
    """Check configuration file availability and readability."""
    config_path = config.config_file
    if not config_path.exists():
        return CheckResult(
            name="config",
            status=CheckStatus.WARN,
            message=f"not found at {config_path} (using defaults)",
            details={"path": str(config_path), "exists": False},
            hint="Run `stata-mcp config cli set` to create and populate config.toml.",
        )

    try:
        _ = config.read_config_text()
        config_data = config.config
        return CheckResult(
            name="config",
            status=CheckStatus.PASS,
            message=f"{config_path} (loaded)",
            details={
                "path": str(config_path),
                "exists": True,
                "sections": sorted(config_data.keys()),
            },
        )
    except Exception as error:
        return CheckResult(
            name="config",
            status=CheckStatus.FAIL,
            message=f"read error: {error}",
            details={"path": str(config_path), "exists": True},
            hint="Fix file permissions or file content encoding.",
        )


def check_working_dir(config: Any) -> CheckResult:
    """Check working directory and required subdirectories."""
    try:
        work_dir = config.WORKING_DIR
        folder = config.STATA_MCP_FOLDER
    except Exception as error:
        return CheckResult(
            name="working_dir",
            status=CheckStatus.FAIL,
            message=f"configuration access error: {error}",
            details={},
            hint="Fix WORKING_DIR-related configuration values.",
        )
    directories = {
        "working_dir": work_dir,
        "stata_mcp_folder": folder.path,
        "log_dir": folder.LOG,
        "dofile_dir": folder.DO,
        "tmp_dir": folder.TMP,
    }

    writable = True
    states: dict[str, dict[str, Any]] = {}
    for key, path in directories.items():
        state = {"path": str(path), "exists": path.exists(), "writable": False}
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".doctor_write_test"
            test_file.touch()
            test_file.unlink()
            state["exists"] = True
            state["writable"] = True
        except (OSError, PermissionError):
            writable = False
        states[key] = state

    return CheckResult(
        name="working_dir",
        status=CheckStatus.PASS if writable else CheckStatus.WARN,
        message=f"{work_dir} ({'writable' if writable else 'fallback may be used'})",
        details=states,
        hint=None if writable else "Set STATA_MCP__CWD to a writable directory.",
    )


def check_guard(config: Any) -> CheckResult:
    """Check guard initialization and blacklist availability."""
    guard_enabled = config.IS_GUARD
    try:
        from ..guard import GuardValidator

        validator = GuardValidator()
        rules_count = len(validator.dangerous_commands) + len(validator.dangerous_patterns)
        return CheckResult(
            name="guard",
            status=CheckStatus.PASS,
            message=f"{'enabled' if guard_enabled else 'disabled'}, loaded {rules_count} rules",
            details={
                "enabled": guard_enabled,
                "command_rules": len(validator.dangerous_commands),
                "pattern_rules": len(validator.dangerous_patterns),
            },
        )
    except Exception as error:
        return CheckResult(
            name="guard",
            status=CheckStatus.FAIL,
            message=f"load error: {error}",
            details={"enabled": guard_enabled},
            hint="Guard module failed to initialize. Reinstall stata-mcp if needed.",
        )


def check_monitor(config: Any) -> CheckResult:
    """Check monitor settings and psutil availability."""
    try:
        import psutil  # noqa: F401

        psutil_available = True
    except ImportError:
        psutil_available = False

    monitor_enabled = config.IS_MONITOR
    ram_limit_mb = config.MAX_RAM_MB

    if monitor_enabled and not psutil_available:
        return CheckResult(
            name="monitor",
            status=CheckStatus.FAIL,
            message="enabled but psutil is not installed",
            details={
                "enabled": monitor_enabled,
                "psutil_available": psutil_available,
                "max_ram_mb": ram_limit_mb,
            },
            hint="Install psutil or disable monitoring.",
        )

    status = CheckStatus.PASS if psutil_available else CheckStatus.WARN
    hint = None if psutil_available else "Install psutil to enable monitor capabilities."
    return CheckResult(
        name="monitor",
        status=status,
        message=(
            f"{'enabled' if monitor_enabled else 'disabled'} "
            f"(psutil {'available' if psutil_available else 'missing'})"
        ),
        details={
            "enabled": monitor_enabled,
            "psutil_available": psutil_available,
            "max_ram_mb": ram_limit_mb,
        },
        hint=hint,
    )


def check_pypi() -> CheckResult:
    """Check connectivity to PyPI."""
    url = "https://pypi.org/pypi/stata-mcp/json"
    start_time = time.monotonic()
    request = Request(url=url, method="HEAD")
    try:
        with urlopen(request, timeout=5) as response:
            status_code = response.status
        elapsed = round(time.monotonic() - start_time, 2)
        return CheckResult(
            name="pypi",
            status=CheckStatus.PASS,
            message=f"reachable ({elapsed}s)",
            details={"url": url, "status_code": status_code, "elapsed_s": elapsed},
        )
    except (URLError, OSError) as error:
        elapsed = round(time.monotonic() - start_time, 2)
        return CheckResult(
            name="pypi",
            status=CheckStatus.WARN,
            message=f"unreachable ({elapsed}s)",
            details={"url": url, "error": str(error), "elapsed_s": elapsed},
            hint="Network issue detected. `stata-mcp update` may fail.",
        )


def _all_checks(config: Any) -> list[tuple[str, Any]]:
    return [
        ("os", check_os),
        ("python", check_python),
        ("uv", check_uv),
        ("dependencies", check_dependencies),
        ("stata_cli", lambda: check_stata_cli(config)),
        ("stata_execution", None),
        ("config", lambda: check_config(config)),
        ("working_dir", lambda: check_working_dir(config)),
        ("guard", lambda: check_guard(config)),
        ("monitor", lambda: check_monitor(config)),
        ("pypi", check_pypi),
    ]


def get_available_checks() -> list[str]:
    """Return available check names."""
    return [name for name, _ in _all_checks(config=None)]


AVAILABLE_CHECKS = get_available_checks()


def run_doctor(config: Any, only_checks: list[str] | None = None) -> DoctorReport:
    """Run selected checks and return a report."""
    try:
        version_text = pkg_version("stata-mcp")
    except PackageNotFoundError:
        version_text = "unknown"

    report = DoctorReport(version=version_text)
    selected = set(only_checks) if only_checks else None
    stata_cli_path: str | None = None

    for check_name, check_func in _all_checks(config):
        if selected is not None and check_name not in selected:
            continue

        try:
            if check_name == "stata_execution":
                if stata_cli_path is None and (
                    selected is not None and "stata_cli" not in selected
                ):
                    stata_cli_result = check_stata_cli(config)
                    stata_cli_path = stata_cli_result.details.get("path")
                result = check_stata_execution(config, stata_cli_path)
            else:
                result = check_func()
                if check_name == "stata_cli":
                    stata_cli_path = result.details.get("path")
        except Exception as error:
            result = CheckResult(
                name=check_name,
                status=CheckStatus.FAIL,
                message=f"unexpected error: {error}",
                details={},
                hint="Run with --verbose and inspect environment-specific configuration.",
            )
        report.checks.append(result)

    return report


def format_report_text(report: DoctorReport, verbose: bool = False) -> str:
    """Format report as readable CLI text."""
    lines: list[str] = [f"stata-mcp v{report.version} — Doctor Report", ""]

    labels = {
        CheckStatus.PASS: "PASS",
        CheckStatus.FAIL: "FAIL",
        CheckStatus.WARN: "WARN",
        CheckStatus.SKIP: "SKIP",
    }

    for check in report.checks:
        lines.append(f"  [{labels[check.status]}] {check.name}: {check.message}")
        if verbose and check.details:
            for key, value in check.details.items():
                lines.append(f"         {key}: {value}")
        if check.hint:
            lines.append(f"         Hint: {check.hint}")

    passed = sum(1 for c in report.checks if c.status == CheckStatus.PASS)
    skipped = sum(1 for c in report.checks if c.status == CheckStatus.SKIP)
    lines.extend(
        [
            "",
            (
                f"Summary: {passed} passed, {report.failure_count} failed, "
                f"{report.warning_count} warning(s), {skipped} skipped"
            ),
        ]
    )
    return "\n".join(lines)
