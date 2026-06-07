"""Tests for shared validation of values interpolated into Stata commands."""

import importlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from stata_mcp.guard import (
    validate_ado_package_name,
    validate_ado_install_request,
    validate_github_repository_allowed,
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


def test_low_level_installers_are_not_exported_from_public_stata_module() -> None:
    stata_module = importlib.import_module("stata_mcp.stata")

    assert not hasattr(stata_module, "SSC_Install")
    assert not hasattr(stata_module, "NET_Install")
    assert not hasattr(stata_module, "GITHUB_Install")


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
@pytest.mark.parametrize("package", ["reghdfe", "ivreg2", "123abc", "  abc123  "])
def test_validate_ado_package_name_accepts_only_ascii_alphanumeric(
    source: str,
    package: str,
) -> None:
    assert validate_ado_package_name(package, source=source) == package.strip()


@pytest.mark.parametrize("source", ["ssc", "net"])
@pytest.mark.parametrize(
    "package",
    ["", "_pkg", "pkg_name", "pkg-name", "pkg.name", "pkg shell", "包名"],
)
def test_validate_ado_package_name_rejects_non_alphanumeric(
    source: str,
    package: str,
) -> None:
    with pytest.raises(ValueError, match="only ASCII letters and numbers"):
        validate_ado_package_name(package, source=source)


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


def test_validate_github_repository_requires_exact_allowlist() -> None:
    assert validate_github_repository_allowed(
        "SepineTam/TexIV",
        allowed_repositories=["sepinetam/texiv"],
    ) == "SepineTam/TexIV"

    with pytest.raises(PermissionError, match="not allowlisted"):
        validate_github_repository_allowed(
            "SepineTam/TexIV",
            allowed_repositories=["SepineTam/Other"],
        )


def test_validate_net_source_location_requires_safe_https_url() -> None:
    assert (
        validate_net_source_location("https://example.com/stata")
        == "https://example.com/stata"
    )

    for unsafe_location in (
        'https://example.com/stata") shell echo pwn',
        "https://example.com/stata,replace",
        "`location'",
        "$location",
        "/srv/stata/packages",
        "http://example.com/stata",
        "ftp://example.com/stata",
        "file:///srv/stata/packages",
        "https://user:password@example.com/stata",
        "https://example.com/stata?package=unsafe",
        "https://example.com/stata#fragment",
        "https://example.com:8443/stata",
        "https://example.com/stata&shell",
        "https://example.com/stata/../private",
        "https://example.com/stata//other",
        "https://127.0.0.1/stata",
    ):
        with pytest.raises(ValueError):
            validate_net_source_location(unsafe_location)


def test_validate_complete_install_request_rejects_source_for_non_net() -> None:
    with pytest.raises(ValueError, match="only valid"):
        validate_ado_install_request(
            "reghdfe",
            "ssc",
            "https://example.com/stata",
        )


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
    if installer_cls is GITHUB_Install:
        monkeypatch.setattr(
            installer_cls,
            "IS_EXIST_GITHUB",
            property(lambda self: True),
        )

    install_kwargs = {"confirm": True}
    if installer_cls is GITHUB_Install:
        install_kwargs["allowed_repositories"] = ["SepineTam/TexIV"]
    installer.install(package, *install_args, **install_kwargs)

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

    install_kwargs = {"confirm": True}
    if installer_cls is GITHUB_Install:
        install_kwargs["allowed_repositories"] = ["SepineTam/TexIV"]
    with pytest.raises(ValueError):
        installer.install(package, *install_args, **install_kwargs)

    controller.run.assert_not_called()


@pytest.mark.parametrize(
    ("installer_cls", "package", "install_args"),
    [
        (SSC_Install, "reghdfe", ()),
        (GITHUB_Install, "SepineTam/TexIV", ()),
        (NET_Install, "custompkg", ("https://example.com/stata",)),
    ],
)
def test_installers_require_confirmation_before_controller_run(
    monkeypatch: pytest.MonkeyPatch,
    installer_cls,
    package: str,
    install_args: tuple[str, ...],
) -> None:
    controller = SimpleNamespace(run=Mock())
    monkeypatch.setattr(installer_cls, "controller", property(lambda self: controller))
    installer = installer_cls.__new__(installer_cls)
    installer.is_replace = False

    with pytest.raises(PermissionError, match="confirm=True"):
        installer.install(package, *install_args)

    controller.run.assert_not_called()


def test_github_installer_does_not_bootstrap_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = SimpleNamespace(run=Mock())
    monkeypatch.setattr(GITHUB_Install, "controller", property(lambda self: controller))
    monkeypatch.setattr(
        GITHUB_Install,
        "IS_EXIST_GITHUB",
        property(lambda self: False),
    )
    installer = GITHUB_Install.__new__(GITHUB_Install)
    installer.is_replace = False

    with pytest.raises(RuntimeError, match="manually"):
        installer.install(
            "SepineTam/TexIV",
            confirm=True,
            allowed_repositories=["SepineTam/TexIV"],
        )

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
    config = SimpleNamespace(
        ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES=("SepineTam/TexIV",),
    )
    monkeypatch.setattr(ado_install_api, "Config", lambda **kwargs: config)
    monkeypatch.setattr(ado_install_api, "create_runtime_context", create_runtime_context)

    with pytest.raises(ValueError):
        ado_install_api.ado_package_install(
            package,
            source=source,
            package_source_from=package_source_from,
        )

    create_runtime_context.assert_not_called()


def test_api_rejects_unallowlisted_github_repository_before_runtime_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_runtime_context = Mock()
    monkeypatch.setattr(
        ado_install_api,
        "Config",
        lambda **kwargs: SimpleNamespace(
            ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES=(),
        ),
    )
    monkeypatch.setattr(ado_install_api, "create_runtime_context", create_runtime_context)

    with pytest.raises(PermissionError, match="not allowlisted"):
        ado_install_api.ado_package_install(
            "SepineTam/TexIV",
            source="github",
        )

    create_runtime_context.assert_not_called()


def test_api_installs_without_enablement_or_caller_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = SimpleNamespace(
        ENABLE_ADO_INSTALL=False,
        ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES=(),
    )
    installer = Mock()
    installer.install.return_value = "Installation State: True"
    installer_cls = Mock(return_value=installer)
    installer_cls.check_installed_from_msg.return_value = True
    monkeypatch.setattr(ado_install_api, "Config", lambda **kwargs: config)
    monkeypatch.setattr(
        ado_install_api,
        "create_runtime_context",
        lambda **kwargs: SimpleNamespace(is_unix=True, stata_cli="stata"),
    )
    monkeypatch.setattr(
        ado_install_api,
        "SOURCE_MAPPING",
        {"ssc": installer_cls},
    )

    result = ado_install_api.ado_package_install("reghdfe")

    assert result == "Installation State: True"
    installer_cls.assert_called_once_with("stata", False, timeout=300)
    installer.install.assert_called_once_with(
        "reghdfe",
        confirm=True,
    )


@pytest.mark.parametrize(
    ("package", "source", "is_replace", "package_source_from", "expected_command"),
    [
        ("reghdfe", "ssc", False, None, "ssc install reghdfe"),
        ("reghdfe", "ssc", True, None, "ssc install reghdfe, replace"),
        (
            "SepineTam/TexIV",
            "github",
            False,
            None,
            "github install SepineTam/TexIV",
        ),
        (
            "custompkg",
            "net",
            False,
            "https://example.com/stata",
            "net install custompkg, from(https://example.com/stata)",
        ),
    ],
)
def test_api_windows_builds_and_verifies_install_command(
    monkeypatch: pytest.MonkeyPatch,
    package: str,
    source: str,
    is_replace: bool,
    package_source_from: str | None,
    expected_command: str,
) -> None:
    config = SimpleNamespace(
        ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES=("SepineTam/TexIV",),
    )
    write_dofile = Mock(return_value="/tmp/install.do")
    stata_do = Mock(return_value={"log_file_path": {"text": "/tmp/install.log"}})
    read_log = Mock(return_value="installation complete")
    monkeypatch.setattr(ado_install_api, "Config", lambda **kwargs: config)
    monkeypatch.setattr(
        ado_install_api,
        "create_runtime_context",
        lambda **kwargs: SimpleNamespace(is_unix=False),
    )
    monkeypatch.setattr(ado_install_api, "write_dofile", write_dofile)
    monkeypatch.setattr(ado_install_api, "_stata_do", stata_do)
    monkeypatch.setattr(ado_install_api, "read_log", read_log)

    result = ado_install_api.ado_package_install(
        package,
        source=source,
        is_replace=is_replace,
        package_source_from=package_source_from,
    )

    assert result.startswith("Installation State: True")
    write_dofile.assert_called_once_with(expected_command, config_file=None)
    stata_do.assert_called_once_with(
        "/tmp/install.do",
        read_log_when_error=False,
        config_file=None,
        allow_package_management=True,
    )
    read_log.assert_called_once_with(
        "/tmp/install.log",
        output_format="core",
        config_file=None,
    )


def test_api_windows_reports_failed_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = SimpleNamespace(
        ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES=(),
    )
    monkeypatch.setattr(ado_install_api, "Config", lambda **kwargs: config)
    monkeypatch.setattr(
        ado_install_api,
        "create_runtime_context",
        lambda **kwargs: SimpleNamespace(is_unix=False),
    )
    monkeypatch.setattr(ado_install_api, "write_dofile", lambda *args, **kwargs: "/tmp/install.do")
    monkeypatch.setattr(
        ado_install_api,
        "_stata_do",
        lambda *args, **kwargs: {"log_file_path": {"text": "/tmp/install.log"}},
    )
    monkeypatch.setattr(
        ado_install_api,
        "read_log",
        lambda *args, **kwargs: "package not found\nr(601)",
    )

    result = ado_install_api.ado_package_install("reghdfe")

    assert result.startswith("Installation State: False")
    assert "Failed to install package 'reghdfe'" in result
    assert "r(601)" in result


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("installation complete", True),
        ("installing into /ado/plus", True),
        ("all files already exist and are up to date", True),
        ("", False),
        ("package not found", False),
        ("could not install\nr(601)", False),
        ("totally failed", False),
    ],
)
def test_net_install_success_detection(message: str, expected: bool) -> None:
    assert NET_Install.check_install(message) is expected
