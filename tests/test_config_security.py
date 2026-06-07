"""Tests for high-risk ado installation configuration."""

from stata_mcp.config import Config


def test_ado_install_security_config_defaults_to_disabled(tmp_path) -> None:
    config = Config(config_file=tmp_path / "missing.toml")

    assert config.ENABLE_ADO_INSTALL is False
    assert config.ADO_INSTALL_ALLOWED_SSC_PACKAGES == ()
    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == ()
    assert config.ADO_INSTALL_ALLOWED_NET_HOSTS == ()
    assert config.ADO_INSTALL_ALLOWED_NET_SOURCES == ()


def test_ado_install_security_config_reads_allowlists(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[SECURITY]
ENABLE_ADO_INSTALL = true
ADO_INSTALL_ALLOWED_SSC_PACKAGES = ["reghdfe"]
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = ["SepineTam/TexIV"]
ADO_INSTALL_ALLOWED_NET_HOSTS = ["packages.example.com"]
ADO_INSTALL_ALLOWED_NET_SOURCES = ["https://packages.example.com/stata"]
""".strip(),
        encoding="utf-8",
    )
    config = Config(config_file=config_path)

    assert config.ENABLE_ADO_INSTALL is True
    assert config.ADO_INSTALL_ALLOWED_SSC_PACKAGES == ("reghdfe",)
    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == ("SepineTam/TexIV",)
    assert config.ADO_INSTALL_ALLOWED_NET_HOSTS == ("packages.example.com",)
    assert config.ADO_INSTALL_ALLOWED_NET_SOURCES == (
        "https://packages.example.com/stata",
    )


def test_ado_install_security_config_reads_environment_allowlists(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("STATA_MCP__ENABLE_ADO_INSTALL", "true")
    monkeypatch.setenv("STATA_MCP__ADO_INSTALL_ALLOWED_SSC_PACKAGES", "reghdfe, estout")
    monkeypatch.setenv(
        "STATA_MCP__ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES",
        "SepineTam/TexIV, owner/repository",
    )
    monkeypatch.setenv(
        "STATA_MCP__ADO_INSTALL_ALLOWED_NET_HOSTS",
        "packages.example.com, mirror.example.com",
    )
    monkeypatch.setenv(
        "STATA_MCP__ADO_INSTALL_ALLOWED_NET_SOURCES",
        "https://packages.example.com/stata, https://mirror.example.com/stata",
    )
    config = Config(config_file=tmp_path / "missing.toml")

    assert config.ENABLE_ADO_INSTALL is True
    assert config.ADO_INSTALL_ALLOWED_SSC_PACKAGES == ("reghdfe", "estout")
    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == (
        "SepineTam/TexIV",
        "owner/repository",
    )
    assert config.ADO_INSTALL_ALLOWED_NET_HOSTS == (
        "packages.example.com",
        "mirror.example.com",
    )
    assert config.ADO_INSTALL_ALLOWED_NET_SOURCES == (
        "https://packages.example.com/stata",
        "https://mirror.example.com/stata",
    )


def test_ado_install_security_config_fails_closed_for_invalid_boolean_types(
    tmp_path,
) -> None:
    invalid_values = ["1", "2", '["false"]', "{ value = false }"]

    for invalid_value in invalid_values:
        config_path = tmp_path / f"invalid-{len(invalid_value)}-{invalid_value[0]}.toml"
        config_path.write_text(
            f"[SECURITY]\nENABLE_ADO_INSTALL = {invalid_value}\n",
            encoding="utf-8",
        )

        assert Config(config_file=config_path).ENABLE_ADO_INSTALL is False
