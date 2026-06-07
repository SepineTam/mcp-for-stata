"""Tests for shared validation of values interpolated into Stata commands."""

import importlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from stata_mcp.guard import (
    validate_ado_package_name,
    validate_install_source,
    validate_net_source_location,
    validate_stata_identifier,
)
from stata_mcp.stata.builtin_tools.ado_install import (
    GITHUB_Install,
    NET_Install,
    SSC_Install,
)

ado_install_api = importlib.import_module("stata_mcp.api.ado_install")


@pytest.mark.parametrize("value", ["regress", "_xtreg", "ivreg2", "  regress  "])
def test_validate_stata_identifier_accepts_safe_values(value: str) -> None:
    expected = value.strip()

    assert validate_stata_identifier(value, field_name="Stata command name") == expected


@pytest.mark.parametrize(
    "value",
    ["", "2sls", "regress shell", "regress.do", "regress\nshell", "../regress"],
)
def test_validate_stata_identifier_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(ValueError, match="Invalid Stata command name"):
        validate_stata_identifier(value, field_name="Stata command name")


def test_validate_install_source_rejects_unknown_source() -> None:
    with pytest.raises(ValueError, match="Supported sources"):
        validate_install_source("shell")


@pytest.mark.parametrize("source", ["ssc", "net"])
def test_validate_ado_package_name_uses_stata_identifier_rules(source: str) -> None:
    assert validate_ado_package_name("  reghdfe  ", source=source) == "reghdfe"

    with pytest.raises(ValueError, match="Invalid ado package name"):
        validate_ado_package_name("reghdfe, replace shell", source=source)


def test_validate_github_repository_allows_only_owner_repository() -> None:
    assert (
        validate_ado_package_name("  SepineTam/TexIV  ", source="github")
        == "SepineTam/TexIV"
    )

    for unsafe_repository in (
        "SepineTam",
        "SepineTam/TexIV shell",
        "SepineTam/TexIV,replace",
        "SepineTam/../TexIV",
    ):
        with pytest.raises(ValueError, match="Invalid GitHub repository"):
            validate_ado_package_name(unsafe_repository, source="github")


def test_validate_net_source_location_rejects_stata_syntax() -> None:
    assert (
        validate_net_source_location("https://example.com/stata")
        == "https://example.com/stata"
    )
    assert validate_net_source_location("/srv/stata/packages") == "/srv/stata/packages"

    for unsafe_location in (
        'https://example.com/stata") shell echo pwn',
        "https://example.com/stata,replace",
        "`location'",
        "$location",
    ):
        with pytest.raises(ValueError, match="Invalid net package source location"):
            validate_net_source_location(unsafe_location)


@pytest.mark.parametrize(
    ("installer_cls", "package", "install_args", "expected_command"),
    [
        (SSC_Install, "  reghdfe  ", (), "ssc install reghdfe, replace"),
        (
            GITHUB_Install,
            "  SepineTam/TexIV  ",
            (),
            "github install SepineTam/TexIV, replace",
        ),
        (
            NET_Install,
            "  custompkg  ",
            ("https://example.com/stata",),
            "net install custompkg, replace from(https://example.com/stata)",
        ),
    ],
)
def test_installers_validate_and_normalize_before_controller_run(
    monkeypatch: pytest.MonkeyPatch,
    installer_cls,
    package: str,
    install_args: tuple[str, ...],
    expected_command: str,
) -> None:
    controller = SimpleNamespace(run=Mock(return_value="installation complete"))
    monkeypatch.setattr(installer_cls, "controller", property(lambda self: controller))
    installer = installer_cls.__new__(installer_cls)
    installer.is_replace = True

    installer.install(package, *install_args)

    controller.run.assert_called_once_with(expected_command)


@pytest.mark.parametrize(
    ("installer_cls", "package", "install_args"),
    [
        (SSC_Install, "reghdfe\nshell echo pwn", ()),
        (GITHUB_Install, "SepineTam/TexIV, shell echo pwn", ()),
        (
            NET_Install,
            "custompkg",
            ('https://example.com/stata") shell echo pwn',),
        ),
    ],
)
def test_installers_reject_unsafe_values_before_controller_run(
    monkeypatch: pytest.MonkeyPatch,
    installer_cls,
    package: str,
    install_args: tuple[str, ...],
) -> None:
    controller = SimpleNamespace(run=Mock())
    monkeypatch.setattr(installer_cls, "controller", property(lambda self: controller))
    installer = installer_cls.__new__(installer_cls)
    installer.is_replace = True

    with pytest.raises(ValueError):
        installer.install(package, *install_args)

    controller.run.assert_not_called()


@pytest.mark.parametrize(
    ("package", "source", "package_source_from"),
    [
        ("reghdfe\nshell echo pwn", "ssc", None),
        ("SepineTam/TexIV, shell echo pwn", "github", None),
        ("custompkg", "net", 'https://example.com/stata") shell echo pwn'),
        ("reghdfe", "unknown", None),
    ],
)
def test_api_rejects_unsafe_install_input_before_runtime_creation(
    monkeypatch: pytest.MonkeyPatch,
    package: str,
    source: str,
    package_source_from: str | None,
) -> None:
    create_runtime_context = Mock()
    monkeypatch.setattr(ado_install_api, "create_runtime_context", create_runtime_context)

    with pytest.raises(ValueError):
        ado_install_api.ado_package_install(
            package,
            source=source,
            package_source_from=package_source_from,
        )

    create_runtime_context.assert_not_called()
