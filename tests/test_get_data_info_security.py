import importlib
import json
import logging
from pathlib import Path

from stata_mcp.api import get_data_info as api_get_data_info
from stata_mcp.config import Config


def _write_config(
    tmp_path: Path,
    working_dir: Path,
    *,
    enable_guard: bool | None = None,
    allowed_domains: list[str] | None = None,
) -> Path:
    config_path = tmp_path / "config.toml"
    lines = [
        "[PROJECT]",
        f'WORKING_DIR = "{working_dir.as_posix()}"',
    ]
    if enable_guard is not None or allowed_domains is not None:
        lines.append("")
        lines.append("[BETA]")
        if enable_guard is not None:
            lines.append(f"enable_data_info_url_guard = {str(enable_guard).lower()}")
        if allowed_domains is not None:
            domains = ", ".join(f'"{domain}"' for domain in allowed_domains)
            lines.append(f"data_info_allowed_url_domains = [{domains}]")

    config_path.write_text("\n".join(lines), encoding="utf-8")
    return config_path


class _FakeDataInfo:
    calls: list[dict] = []

    def __init__(
        self,
        data_path,
        vars_list=None,
        *,
        encoding: str = "utf-8",
        cache_dir=None,
        head: int = 0,
    ):
        self.data_path = data_path
        self.vars_list = vars_list
        self.encoding = encoding
        self.cache_dir = cache_dir
        self.head = head
        self.calls.append(
            {
                "data_path": data_path,
                "vars_list": vars_list,
                "encoding": encoding,
                "cache_dir": cache_dir,
                "head": head,
            }
        )

    @property
    def info(self):
        return {
            "overview": {
                "source": str(self.data_path),
            },
            "head": self.head,
        }


def _patch_fake_data_info(monkeypatch):
    _FakeDataInfo.calls = []
    get_data_info_module = importlib.import_module("stata_mcp.api.get_data_info")

    def fake_get_data_handler(extension: str):
        if extension == "csv":
            return _FakeDataInfo
        return None

    monkeypatch.setattr(
        get_data_info_module,
        "get_data_handler",
        fake_get_data_handler,
    )
    return _FakeDataInfo


def _joined_log_messages(caplog) -> str:
    return "\n".join(caplog.messages)


def test_local_file_within_working_dir_is_allowed(tmp_path) -> None:
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    data_path = working_dir / "data.csv"
    data_path.write_text("x,y\n1,2\n", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir)

    result = api_get_data_info(
        data_path=data_path.as_posix(),
        config_file=config_path,
    )

    payload = json.loads(result)
    assert payload["overview"]["source"] == data_path.resolve().as_posix()


def test_local_file_outside_working_dir_is_rejected(tmp_path) -> None:
    working_dir = tmp_path / "work"
    outside_dir = tmp_path / "outside"
    working_dir.mkdir()
    outside_dir.mkdir()
    data_path = outside_dir / "data.csv"
    data_path.write_text("x,y\n1,2\n", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir)

    result = api_get_data_info(
        data_path=data_path.as_posix(),
        config_file=config_path,
    )

    assert result == "Access denied: data file must be within the working directory."


def test_local_file_outside_working_dir_logs_security_violation(
    caplog,
    tmp_path,
) -> None:
    working_dir = tmp_path / "work"
    outside_dir = tmp_path / "outside"
    working_dir.mkdir()
    outside_dir.mkdir()
    data_path = outside_dir / "data.csv"
    data_path.write_text("x,y\n1,2\n", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir)

    with caplog.at_level(logging.WARNING):
        result = api_get_data_info(
            data_path=data_path.as_posix(),
            config_file=config_path,
        )

    messages = _joined_log_messages(caplog)
    assert result == "Access denied: data file must be within the working directory."
    assert "[SECURITY VIOLATION]" in messages
    assert "resolved_path" in messages


def test_relative_local_file_is_resolved_from_working_dir(
    monkeypatch,
    tmp_path,
) -> None:
    working_dir = tmp_path / "work"
    process_dir = tmp_path / "process"
    working_dir.mkdir()
    process_dir.mkdir()
    data_path = working_dir / "data.csv"
    data_path.write_text("x,y\n1,2\n", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir)
    monkeypatch.chdir(process_dir)

    result = api_get_data_info(
        data_path="data.csv",
        config_file=config_path,
    )

    payload = json.loads(result)
    assert payload["overview"]["source"] == data_path.resolve().as_posix()


def test_url_guard_disabled_does_not_block_non_allowlisted_domain(
    monkeypatch,
    tmp_path,
) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(tmp_path, working_dir, enable_guard=False)

    result = api_get_data_info(
        data_path="https://evil.com/data.csv",
        config_file=config_path,
    )

    payload = json.loads(result)
    assert payload["overview"]["source"] == "https://evil.com/data.csv"
    assert fake_data_info.calls[0]["data_path"] == "https://evil.com/data.csv"


def test_url_guard_enabled_allows_allowlisted_domain(
    monkeypatch,
    tmp_path,
) -> None:
    _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(
        tmp_path,
        working_dir,
        enable_guard=True,
        allowed_domains=["raw.githubusercontent.com"],
    )

    result = api_get_data_info(
        data_path="https://raw.githubusercontent.com/owner/repo/data.csv",
        config_file=config_path,
    )

    payload = json.loads(result)
    assert payload["overview"]["source"] == (
        "https://raw.githubusercontent.com/owner/repo/data.csv"
    )


def test_url_guard_enabled_does_not_special_case_github_raw_domain(
    monkeypatch,
    tmp_path,
) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(
        tmp_path,
        working_dir,
        enable_guard=True,
        allowed_domains=["github.com"],
    )

    result = api_get_data_info(
        data_path="https://raw.githubusercontent.com/owner/repo/data.csv",
        config_file=config_path,
    )

    assert result == "Access denied: URL domain is not in the allowlist."
    assert fake_data_info.calls == []


def test_url_guard_enabled_rejects_non_allowlisted_domain(
    monkeypatch,
    tmp_path,
) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(
        tmp_path,
        working_dir,
        enable_guard=True,
        allowed_domains=["github.com"],
    )

    result = api_get_data_info(
        data_path="https://evil.com/data.csv",
        config_file=config_path,
    )

    assert result == "Access denied: URL domain is not in the allowlist."
    assert fake_data_info.calls == []


def test_url_guard_enabled_rejects_non_allowlisted_domain_logs_security_violation(
    caplog,
    monkeypatch,
    tmp_path,
) -> None:
    _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(
        tmp_path,
        working_dir,
        enable_guard=True,
        allowed_domains=["github.com"],
    )

    with caplog.at_level(logging.WARNING):
        result = api_get_data_info(
            data_path="https://evil.com/data.csv?token=secret",
            config_file=config_path,
        )

    messages = _joined_log_messages(caplog)
    assert result == "Access denied: URL domain is not in the allowlist."
    assert "requested_url='https://evil.com/data.csv'" in messages
    assert "domain-not-in-allowlist" in messages
    assert "token=secret" not in messages


def test_url_guard_enabled_rejects_ip_url(monkeypatch, tmp_path) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(
        tmp_path,
        working_dir,
        enable_guard=True,
        allowed_domains=["example.com"],
    )

    result = api_get_data_info(
        data_path="https://192.168.1.1/data.csv",
        config_file=config_path,
    )

    assert result == "Access denied: IP-based URLs are not allowed."
    assert fake_data_info.calls == []


def test_url_guard_enabled_rejects_ip_url_logs_security_violation(
    caplog,
    monkeypatch,
    tmp_path,
) -> None:
    _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(
        tmp_path,
        working_dir,
        enable_guard=True,
        allowed_domains=["example.com"],
    )

    with caplog.at_level(logging.WARNING):
        result = api_get_data_info(
            data_path="https://192.168.1.1/data.csv",
            config_file=config_path,
        )

    messages = _joined_log_messages(caplog)
    assert result == "Access denied: IP-based URLs are not allowed."
    assert "[SECURITY VIOLATION]" in messages
    assert "ip-host-not-allowed" in messages


def test_url_guard_enabled_rejects_http_scheme(monkeypatch, tmp_path) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(
        tmp_path,
        working_dir,
        enable_guard=True,
        allowed_domains=["example.com"],
    )

    result = api_get_data_info(
        data_path="http://example.com/data.csv",
        config_file=config_path,
    )

    assert result == "Access denied: only HTTPS URLs are allowed."
    assert fake_data_info.calls == []


def test_url_rejects_username_or_password(monkeypatch, tmp_path) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(
        tmp_path,
        working_dir,
        enable_guard=True,
        allowed_domains=["github.com"],
    )

    result = api_get_data_info(
        data_path="https://evil.com@github.com/data.csv",
        config_file=config_path,
    )

    assert result == "Access denied: URL userinfo is not allowed."
    assert fake_data_info.calls == []


def test_url_rejects_username_or_password_logs_security_violation(
    caplog,
    monkeypatch,
    tmp_path,
) -> None:
    _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(
        tmp_path,
        working_dir,
        enable_guard=True,
        allowed_domains=["github.com"],
    )

    with caplog.at_level(logging.WARNING):
        result = api_get_data_info(
            data_path="https://evil.com@github.com/data.csv",
            config_file=config_path,
        )

    messages = _joined_log_messages(caplog)
    assert result == "Access denied: URL userinfo is not allowed."
    assert "[SECURITY VIOLATION]" in messages
    assert "url-userinfo-not-allowed" in messages


def test_data_info_url_guard_config_ignores_environment(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("STATA_MCP__ENABLE_DATA_INFO_URL_GUARD", "true")
    monkeypatch.setenv("STATA_MCP__DATA_INFO_ALLOWED_URL_DOMAINS", "github.com")
    config = Config(config_file=tmp_path / "missing.toml")

    assert config.ENABLE_DATA_INFO_URL_GUARD is False
    assert config.DATA_INFO_ALLOWED_URL_DOMAINS == ()
