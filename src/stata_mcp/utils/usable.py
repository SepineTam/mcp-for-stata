#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : usable.py

"""
Stata MCP Configuration Check Script
This script automatically checks if your Stata MCP configuration is correct
"""

import os
import platform
import shutil
import subprocess
import sys
import time
from typing import Dict, Optional, Tuple

from ..config import Config
from ..stata import StataFinder

config = Config()


def print_status(message: str, status: bool) -> None:
    """Print a message with status indicator"""
    status_str = "✅ PASSED" if status else "❌ FAILED"
    print(f"{message}: {status_str}")


def print_info(message: str) -> None:
    """Print an info message"""
    print(f"{message}: ℹ️ INFO")


def check_uv() -> Tuple[Optional[str], bool]:
    """Check if uv is installed"""
    uv_path = shutil.which("uv")
    return uv_path, uv_path is not None


def check_os() -> Tuple[str, bool]:
    """Check current operating system"""
    os_mapping = {"Darwin": "macOS", "Windows": "Windows", "Linux": "Linux"}
    detected_os = os_mapping.get(platform.system(), "unknown")
    is_supported = detected_os in os_mapping.values()

    return detected_os, is_supported


def check_python_version() -> Tuple[str, bool]:
    """Check if the Python version is compatible"""
    current_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    is_compatible = sys.version_info.major == 3 and sys.version_info.minor >= 11

    return current_version, is_compatible


def test_stata_execution(stata_cli_path: Optional[str]) -> bool:
    """Test if Stata can be executed"""
    if not stata_cli_path or not os.path.exists(stata_cli_path):
        return False

    commands = 'display "Stata-MCP Test"\nexit, STATA\n'

    try:
        if config.IS_UNIX:  # macOS or Linux
            proc = subprocess.Popen(
                [stata_cli_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
            )
            try:
                proc.communicate(input=commands, timeout=10)
                return proc.returncode == 0
            finally:
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()

        else:  # Windows
            # Create a temporary do-file for testing
            temp_do_file = config.STATA_MCP_DIRECTORY / "temp_test.do"

            temp_do_file.write_text(commands)

            # Run Stata with the temp do-file
            cmd = f'"{stata_cli_path}" /e do "{temp_do_file}"'
            result = subprocess.run(cmd, shell=True, timeout=10)

            # Clean up
            if temp_do_file.exists():
                temp_do_file.unlink()

            return result.returncode == 0

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
        print(f"  Error testing Stata: {e}")
        return False


def check_directories() -> Dict[str, Tuple[str, bool]]:
    """Check if required directories exist and create them if needed"""
    home_dir = os.path.expanduser("~")
    documents_path = os.path.join(home_dir, "Documents")

    # Define directories that should exist
    base_path = os.path.join(documents_path, "stata-mcp-folder")
    dirs = {
        "base_dir": (base_path, False),
        "log_dir": (os.path.join(base_path, "stata-mcp-log"), False),
        "dofile_dir": (os.path.join(base_path, "stata-mcp-dofile"), False),
        "result_dir": (os.path.join(base_path, "stata-mcp-result"), False),
    }

    # Check and create directories if they don't exist
    for name, (path, _) in dirs.items():
        exists = os.path.exists(path)
        if not exists:
            try:
                os.makedirs(path, exist_ok=True)
                exists = True
                print(f"  Created directory: {path}")
            except Exception as e:
                print(f"  Error creating directory {path}: {e}")

        is_writable = os.access(path, os.W_OK) if exists else False
        dirs[name] = (path, exists and is_writable)

    return dirs


def animate_loading(seconds: int) -> None:
    """Display an animated loading spinner"""
    chars = "|/-\\"
    for _ in range(seconds * 5):
        for char in chars:
            sys.stdout.write(f"\r  Finding Stata CLI {char} ")
            sys.stdout.flush()
            time.sleep(0.05)
    sys.stdout.write("\r" + " " * 20 + "\r")
    sys.stdout.flush()


def usable() -> int:
    """Main function to check Stata MCP configuration"""
    print("\n===== Stata MCP Configuration Check =====\n")

    # Check operating system
    detected_os, os_supported = check_os()
    print_status(f"Operating system (Current: {detected_os})", os_supported)
    if not os_supported:
        print(
            "  Warning: Your operating system may not be fully supported by Stata-MCP."
        )

    # Check uv first, then fall back to Python
    uv_path, uv_installed = check_uv()
    python_compatible = True  # Default to True, will be set to False if no uv and Python < 3.11

    if uv_installed:
        print_status(f"uv (Path: {uv_path})", True)
    else:
        print_info("uv (not found, will check Python instead)")
        # Check Python version
        python_version, python_compatible = check_python_version()
        print_status(
            f"Python version (Current: {python_version})",
            python_compatible)
        if not python_compatible:
            print("  Warning: Python 3.11+ is required for Stata-MCP without uv.")

    # Find Stata CLI
    print("Locating Stata CLI...")
    animate_loading(2)  # Show loading animation for 2 seconds
    stata_cli_path = StataFinder().STATA_CLI

    stata_found = bool(stata_cli_path and os.path.exists(stata_cli_path))
    print_status(
        f"Stata CLI (Path: {stata_cli_path or 'Not found'})",
        stata_found)

    # Test Stata execution if found
    stata_works = False
    if stata_found:
        print("Testing Stata execution...")
        stata_works = test_stata_execution(stata_cli_path)
        print_status("Stata execution test", stata_works)
        if not stata_works:
            print("  Warning: Stata was found but could not be executed properly.")
            print(
                "  You may need to specify the path manually in config.py or as an environment variable."
            )

    # Check and create necessary directories
    print("\nChecking required directories...")
    directories = check_directories()
    all_dirs_ok = True
    for name, (path, exists) in directories.items():
        dir_name = name.replace("_", " ").title()
        print_status(f"{dir_name} (Path: {path})", exists)
        if not exists:
            all_dirs_ok = False
            print(f"  Warning: Could not create or access {path}")

    # Overall summary
    print("\n===== Summary =====")

    # Environment is OK if: (uv installed) OR (Python >= 3.11)
    env_ok = uv_installed or python_compatible

    all_passed = (
        os_supported
        and env_ok
        and stata_found
        and stata_works
        and all_dirs_ok
    )

    if all_passed:
        print("\n✅ Success! Your Stata-MCP setup is ready to use.")
        print(
            "You can now use Stata-MCP with your preferred MCP client (Claude, Cherry Studio, etc.)"
        )
    else:
        print(
            "\n⚠️ Some checks failed. Please address the issues above to use Stata-MCP."
        )
        if not stata_found or not stata_works:
            print(
                "\nTo manually specify your Stata path, add this to your MCP configuration:"
            )
            print('  "env": {')
            print('    "STATA_CLI": "/path/to/your/stata/executable"')
            print("  }")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(usable())
