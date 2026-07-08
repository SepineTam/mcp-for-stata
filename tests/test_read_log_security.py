import os
from pathlib import Path

from stata_mcp.api.read_log import read_log


def _write_config(tmp_path: Path, working_dir: Path, *, strict_boundary: bool) -> Path:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[PROJECT]",
                f'WORKING_DIR = "{working_dir.as_posix()}"',
                "",
                "[SECURITY]",
                f"strict_read_log_boundary = {str(strict_boundary).lower()}",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def test_strict_true_allows_file_in_statamcp_folder(tmp_path: Path) -> None:
    working_dir = tmp_path / "work"
    statamcp_dir = working_dir / ".statamcp"
    log_dir = statamcp_dir / "stata-mcp-log"
    log_dir.mkdir(parents=True)
    log_file = log_dir / "test.log"
    log_file.write_text("log content", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir, strict_boundary=True)

    result = read_log(log_file.as_posix(), config_file=config_path)

    assert result == "log content"


def test_strict_true_denies_file_in_working_dir_root(tmp_path: Path) -> None:
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    log_file = working_dir / "test.log"
    log_file.write_text("log content", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir, strict_boundary=True)

    result = read_log(log_file.as_posix(), config_file=config_path)

    assert result == "Access denied: log file must be within the stata-mcp folder."


def test_strict_true_denies_file_outside_working_dir(tmp_path: Path) -> None:
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    outside_file = tmp_path / "outside.log"
    outside_file.write_text("log content", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir, strict_boundary=True)

    result = read_log(outside_file.as_posix(), config_file=config_path)

    assert result == "Access denied: log file must be within the stata-mcp folder."


def test_strict_true_denies_parent_directory_escape(tmp_path: Path) -> None:
    working_dir = tmp_path / "work"
    statamcp_dir = working_dir / ".statamcp"
    log_dir = statamcp_dir / "stata-mcp-log"
    log_dir.mkdir(parents=True)
    outside_file = tmp_path / "secret.log"
    outside_file.write_text("secret", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir, strict_boundary=True)

    escaped_path = log_dir / ".." / ".." / ".." / "secret.log"
    result = read_log(escaped_path.as_posix(), config_file=config_path)

    assert result == "Access denied: log file must be within the stata-mcp folder."


def test_strict_true_denies_symlink_to_outside_file(tmp_path: Path) -> None:
    working_dir = tmp_path / "work"
    statamcp_dir = working_dir / ".statamcp"
    log_dir = statamcp_dir / "stata-mcp-log"
    log_dir.mkdir(parents=True)
    outside_file = tmp_path / "outside.log"
    outside_file.write_text("log content", encoding="utf-8")
    symlink_file = log_dir / "link.log"
    symlink_file.symlink_to(outside_file)
    config_path = _write_config(tmp_path, working_dir, strict_boundary=True)

    result = read_log(symlink_file.as_posix(), config_file=config_path)

    assert result == "Access denied: log file must be within the stata-mcp folder."


def test_strict_false_allows_file_anywhere(tmp_path: Path) -> None:
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    outside_file = tmp_path / "outside.log"
    outside_file.write_text("log content", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir, strict_boundary=False)

    result = read_log(outside_file.as_posix(), config_file=config_path)

    assert result == "log content"


def test_env_var_cannot_override_strict_read_log_boundary(tmp_path: Path, monkeypatch) -> None:
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    outside_file = tmp_path / "outside.log"
    outside_file.write_text("log content", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir, strict_boundary=False)
    monkeypatch.setenv("STATA_MCP__STRICT_READ_LOG_BOUNDARY", "true")

    result = read_log(outside_file.as_posix(), config_file=config_path)

    assert result == "log content"
    assert os.getenv("STATA_MCP__STRICT_READ_LOG_BOUNDARY") == "true"
