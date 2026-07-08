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


def test_async_do_beta_config_reads_true_false_values(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[BETA]
IS_ASYNC_DO = "true"
""".strip(),
        encoding="utf-8",
    )

    assert Config(config_file=config_path).IS_ASYNC_DO is True

    monkeypatch.setenv("STATA_MCP__IS_ASYNC_DO", "false")
    assert Config(config_file=config_path).IS_ASYNC_DO is False


def test_async_do_beta_config_rejects_on_off_values(monkeypatch, tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[BETA]
IS_ASYNC_DO = "on"
""".strip(),
        encoding="utf-8",
    )

    assert Config(config_file=config_path).IS_ASYNC_DO is False

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


def test_project_config_overrides_user_config_for_regular_sections(
    monkeypatch,
    tmp_path,
) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    user_config_dir = home_dir / ".statamcp"
    project_config_dir = project_dir / ".statamcp"
    user_config_dir.mkdir(parents=True)
    project_config_dir.mkdir(parents=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.chdir(project_dir)

    (user_config_dir / "config.toml").write_text(
        """
[BETA]
MAX_ASYNC_DO = 2
""".strip(),
        encoding="utf-8",
    )
    (project_config_dir / "config.toml").write_text(
        """
[BETA]
MAX_ASYNC_DO = 5
""".strip(),
        encoding="utf-8",
    )

    config = Config()

    assert config.MAX_ASYNC_DO == 5


def test_user_config_overrides_project_config_for_security_sections(
    monkeypatch,
    tmp_path,
) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    user_config_dir = home_dir / ".statamcp"
    project_config_dir = project_dir / ".statamcp"
    user_config_dir.mkdir(parents=True)
    project_config_dir.mkdir(parents=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.chdir(project_dir)

    (user_config_dir / "config.toml").write_text(
        """
[SECURITY]
IS_GUARD = true
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = ["trusted/repository"]
""".strip(),
        encoding="utf-8",
    )
    (project_config_dir / "config.toml").write_text(
        """
[SECURITY]
IS_GUARD = false
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = ["project/repository"]
""".strip(),
        encoding="utf-8",
    )

    config = Config()

    assert config.IS_GUARD is True
    assert config.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES == ("trusted/repository",)


def test_debug_config_file_ignores_user_and_project_config(
    monkeypatch,
    tmp_path,
) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    user_config_dir = home_dir / ".statamcp"
    project_config_dir = project_dir / ".statamcp"
    user_config_dir.mkdir(parents=True)
    project_config_dir.mkdir(parents=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.chdir(project_dir)

    (user_config_dir / "config.toml").write_text(
        """
[BETA]
MAX_ASYNC_DO = 2
""".strip(),
        encoding="utf-8",
    )
    (project_config_dir / "config.toml").write_text(
        """
[BETA]
MAX_ASYNC_DO = 5
""".strip(),
        encoding="utf-8",
    )
    debug_config = tmp_path / "debug.toml"
    debug_config.write_text(
        """
[BETA]
MAX_ASYNC_DO = 7
""".strip(),
        encoding="utf-8",
    )

    config = Config(config_file=debug_config)

    assert config.is_debug_config is True
    assert config.config_files == (debug_config,)
    assert config.MAX_ASYNC_DO == 7


def test_linux_system_config_overrides_user_project_and_environment(
    monkeypatch,
    tmp_path,
) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    system_config = tmp_path / "etc" / "statamcp" / "config.toml"
    user_config_dir = home_dir / ".statamcp"
    project_config_dir = project_dir / ".statamcp"
    user_config_dir.mkdir(parents=True)
    project_config_dir.mkdir(parents=True)
    system_config.parent.mkdir(parents=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(Config, "SYSTEM_CONFIG_FILE", system_config)
    monkeypatch.setenv("STATA_MCP__MAX_ASYNC_DO", "9")
    monkeypatch.chdir(project_dir)

    (user_config_dir / "config.toml").write_text(
        """
[BETA]
MAX_ASYNC_DO = 2
""".strip(),
        encoding="utf-8",
    )
    (project_config_dir / "config.toml").write_text(
        """
[BETA]
MAX_ASYNC_DO = 5
""".strip(),
        encoding="utf-8",
    )
    system_config.write_text(
        """
[BETA]
MAX_ASYNC_DO = 4
""".strip(),
        encoding="utf-8",
    )

    config = Config()

    assert config.system_config_file == system_config
    assert config.MAX_ASYNC_DO == 4


def test_data_info_url_guard_beta_config_merges_user_project_and_system(
    monkeypatch,
    tmp_path,
) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    system_config = tmp_path / "etc" / "statamcp" / "config.toml"
    user_config_dir = home_dir / ".statamcp"
    project_config_dir = project_dir / ".statamcp"
    user_config_dir.mkdir(parents=True)
    project_config_dir.mkdir(parents=True)
    system_config.parent.mkdir(parents=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(Config, "SYSTEM_CONFIG_FILE", system_config)
    monkeypatch.chdir(project_dir)

    (user_config_dir / "config.toml").write_text(
        """
[BETA]
enable_data_info_url_guard = false
data_info_allowed_url_domains = ["user.example.com"]
""".strip(),
        encoding="utf-8",
    )
    (project_config_dir / "config.toml").write_text(
        """
[BETA]
enable_data_info_url_guard = true
data_info_allowed_url_domains = ["project.example.com"]
""".strip(),
        encoding="utf-8",
    )
    system_config.write_text(
        """
[BETA]
data_info_allowed_url_domains = ["system.example.com"]
""".strip(),
        encoding="utf-8",
    )

    config = Config()

    assert config.ENABLE_DATA_INFO_URL_GUARD is True
    assert config.DATA_INFO_ALLOWED_URL_DOMAINS == ("system.example.com",)


def test_linux_system_config_overrides_debug_config(
    monkeypatch,
    tmp_path,
) -> None:
    system_config = tmp_path / "etc" / "statamcp" / "config.toml"
    debug_config = tmp_path / "debug.toml"
    system_config.parent.mkdir(parents=True)
    monkeypatch.setattr("platform.system", lambda: "Linux")
    monkeypatch.setattr(Config, "SYSTEM_CONFIG_FILE", system_config)

    debug_config.write_text(
        """
[BETA]
MAX_ASYNC_DO = 7
""".strip(),
        encoding="utf-8",
    )
    system_config.write_text(
        """
[BETA]
MAX_ASYNC_DO = 4
""".strip(),
        encoding="utf-8",
    )

    config = Config(config_file=debug_config)

    assert config.config_files == (debug_config, system_config)
    assert config.MAX_ASYNC_DO == 4


def test_system_config_is_ignored_on_non_linux(
    monkeypatch,
    tmp_path,
) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"
    system_config = tmp_path / "etc" / "statamcp" / "config.toml"
    project_config_dir = project_dir / ".statamcp"
    project_config_dir.mkdir(parents=True)
    system_config.parent.mkdir(parents=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr("platform.system", lambda: "Darwin")
    monkeypatch.setattr(Config, "SYSTEM_CONFIG_FILE", system_config)
    monkeypatch.chdir(project_dir)

    (project_config_dir / "config.toml").write_text(
        """
[BETA]
MAX_ASYNC_DO = 5
""".strip(),
        encoding="utf-8",
    )
    system_config.write_text(
        """
[BETA]
MAX_ASYNC_DO = 4
""".strip(),
        encoding="utf-8",
    )

    config = Config()

    assert config.system_config_file is None
    assert config.MAX_ASYNC_DO == 5
