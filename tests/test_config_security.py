"""Tests for high-risk ado installation configuration."""

from stata_mcp.config import Config


def test_ado_install_security_config_defaults_to_disabled(tmp_path) -> None:
    config = Config(config_file=tmp_path / "missing.toml")

    assert config.ENABLE_ADO_INSTALL is False
    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == ()


def test_ado_install_security_config_reads_github_allowlist(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[SECURITY]
ENABLE_ADO_INSTALL = true
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = ["SepineTam/TexIV"]
""".strip(),
        encoding="utf-8",
    )
    config = Config(config_file=config_path)

    assert config.ENABLE_ADO_INSTALL is True
    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == ("SepineTam/TexIV",)


def test_ado_install_security_config_reads_environment_github_allowlist(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("STATA_MCP__ENABLE_ADO_INSTALL", "true")
    monkeypatch.setenv(
        "STATA_MCP__ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES",
        "SepineTam/TexIV, owner/repository",
    )
    config = Config(config_file=tmp_path / "missing.toml")

    assert config.ENABLE_ADO_INSTALL is True
    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == (
        "SepineTam/TexIV",
        "owner/repository",
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
