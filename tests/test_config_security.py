"""Tests for high-risk ado installation configuration."""

from stata_mcp.config import Config


def test_ado_install_security_config_defaults_to_disabled(tmp_path) -> None:
    config = Config(config_file=tmp_path / "missing.toml")

    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == ()


def test_ado_install_security_config_reads_github_allowlist(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[SECURITY]
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = ["SepineTam/TexIV"]
""".strip(),
        encoding="utf-8",
    )
    config = Config(config_file=config_path)

    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == ("SepineTam/TexIV",)


def test_ado_install_security_config_reads_environment_github_allowlist(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv(
        "STATA_MCP__ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES",
        "SepineTam/TexIV, owner/repository",
    )
    config = Config(config_file=tmp_path / "missing.toml")

    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == (
        "SepineTam/TexIV",
        "owner/repository",
    )
