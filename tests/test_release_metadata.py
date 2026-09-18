"""Check release metadata shared by PyPI, MCP Registry, and binary builds."""

from __future__ import annotations

import importlib.util
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_registry_name_is_declared_in_pypi_readme():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    readme = (ROOT / project["project"]["readme"]).read_text(encoding="utf-8")

    assert f"mcp-name: {registry['name']}" in readme


def test_registry_versions_match_python_distribution():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))

    assert registry["version"] == project["project"]["version"]
    for package in registry["packages"]:
        if package["registryType"] == "pypi":
            assert package["identifier"] == project["project"]["name"]
            assert package["version"] == project["project"]["version"]


def test_binary_build_inputs_exist():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    options = project["tool"]["nuitka"]

    if "main" in options:
        assert (ROOT / options["main"]).is_file()
    else:
        from stata_mcp.cli import main

        assert callable(main)
        assert project["project"]["scripts"]["stata-mcp"] == "stata_mcp.cli:main"

    for package in options.get("include-package", []):
        assert importlib.util.find_spec(package) is not None, package
