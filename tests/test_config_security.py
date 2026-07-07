"""Tests for high-risk ado installation configuration."""

from stata_mcp.config import Config


def test_ado_install_security_config_defaults_to_disabled(tmp_path) -> None:
    config = Config(config_file=tmp_path / "missing.toml")

    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == ()
    assert config.IS_ASYNC_DO is False
    assert config.MAX_ASYNC_DO == 3


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


def test_async_do_beta_config_reads_on_off_values(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[BETA]
IS_ASYNC_DO = "on"
""".strip(),
        encoding="utf-8",
    )

    assert Config(config_file=config_path).IS_ASYNC_DO is True

    monkeypatch.setenv("STATA_MCP__IS_ASYNC_DO", "off")
    assert Config(config_file=config_path).IS_ASYNC_DO is False


def test_async_do_max_parallel_config_reads_positive_integer(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[BETA]
MAX_ASYNC_DO = 5
""".strip(),
        encoding="utf-8",
    )

    assert Config(config_file=config_path).MAX_ASYNC_DO == 5

    monkeypatch.setenv("STATA_MCP__MAX_ASYNC_DO", "2")
    assert Config(config_file=config_path).MAX_ASYNC_DO == 2

    monkeypatch.setenv("STATA_MCP__MAX_ASYNC_DO", "0")
    assert Config(config_file=config_path).MAX_ASYNC_DO == 3


def test_async_do_max_parallel_config_rejects_invalid_values(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[BETA]
MAX_ASYNC_DO = -2
""".strip(),
        encoding="utf-8",
    )

    assert Config(config_file=config_path).MAX_ASYNC_DO == 3

    monkeypatch.setenv("STATA_MCP__MAX_ASYNC_DO", "not-a-number")
    assert Config(config_file=config_path).MAX_ASYNC_DO == 3
