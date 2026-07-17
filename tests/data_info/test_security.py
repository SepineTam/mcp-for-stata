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
    strict_local_boundary: bool | None = None,
    additional_allowed_dirs: list[Path] | None = None,
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
    if strict_local_boundary is not None or additional_allowed_dirs is not None:
        lines.append("")
        lines.append("[SECURITY]")
        if strict_local_boundary is not None:
            lines.append(
                f"strict_data_info_local_boundary = {str(strict_local_boundary).lower()}"
            )
        if additional_allowed_dirs is not None:
            allowed_dirs = ", ".join(
                f'"{allowed_dir.as_posix()}"'
                for allowed_dir in additional_allowed_dirs
            )
            lines.append(f"ADDITIONAL_ALLOWED_DIRS = [{allowed_dirs}]")

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
        is_cache: bool = True,
        metrics=None,
        string_keep_number: int = 10,
        decimal_places: int = 3,
        hash_length: int = 12,
        request_id: str | None = None,
    ):
        self.data_path = data_path
        self.vars_list = vars_list
        self.encoding = encoding
        self.cache_dir = cache_dir
        self.head = head
        self.is_cache = is_cache
        self.metrics = metrics
        self.string_keep_number = string_keep_number
        self.decimal_places = decimal_places
        self.hash_length = hash_length
        self.request_id = request_id
        self.calls.append(
            {
                "data_path": data_path,
                "vars_list": vars_list,
                "encoding": encoding,
                "cache_dir": cache_dir,
                "head": head,
                "is_cache": is_cache,
                "metrics": metrics,
                "string_keep_number": string_keep_number,
                "decimal_places": decimal_places,
                "hash_length": hash_length,
                "request_id": request_id,
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


def test_contextual_data_info_settings_are_passed_to_handler(
    monkeypatch,
    tmp_path,
) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    data_path = working_dir / "data.csv"
    data_path.write_text("x,y\n1,2\n", encoding="utf-8")
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f"""
[PROJECT]
WORKING_DIR = "{working_dir.as_posix()}"

[data_info]
heads = 2

[MCP.TOOLS.DATA_INFO]
is_cache = false
metrics = ["med"]
string_keep_number = 4
decimal_places = 1
hash_length = 8
heads = 7
""".strip(),
        encoding="utf-8",
    )

    api_get_data_info(
        data_path=data_path.as_posix(),
        config_file=config_path,
        tool_context="mcp",
    )

    assert fake_data_info.calls[-1]["is_cache"] is False
    assert fake_data_info.calls[-1]["metrics"] == (
        "obs",
        "mean",
        "stderr",
        "min",
        "max",
        "med",
    )
    assert fake_data_info.calls[-1]["string_keep_number"] == 4
    assert fake_data_info.calls[-1]["decimal_places"] == 1
    assert fake_data_info.calls[-1]["hash_length"] == 8
    assert fake_data_info.calls[-1]["head"] == 7


def test_explicit_head_overrides_contextual_default(monkeypatch, tmp_path) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    data_path = working_dir / "data.csv"
    data_path.write_text("x,y\n1,2\n", encoding="utf-8")
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f"""
[PROJECT]
WORKING_DIR = "{working_dir.as_posix()}"

[MCP.TOOLS.DATA_INFO]
heads = 7
""".strip(),
        encoding="utf-8",
    )

    api_get_data_info(
        data_path=data_path.as_posix(),
        config_file=config_path,
        head=0,
        tool_context="mcp",
    )

    assert fake_data_info.calls[-1]["head"] == 0


def test_local_file_outside_working_dir_is_allowed_by_default(tmp_path) -> None:
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

    payload = json.loads(result)
    assert payload["overview"]["source"] == data_path.resolve().as_posix()


def test_local_file_in_additional_allowed_dir_is_allowed_when_strict(
    monkeypatch,
    tmp_path,
) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    shared_dir = tmp_path / "shared"
    working_dir.mkdir()
    shared_dir.mkdir()
    data_path = shared_dir / "data.csv"
    data_path.write_text("x,y\n1,2\n", encoding="utf-8")
    config_path = _write_config(
        tmp_path,
        working_dir,
        strict_local_boundary=True,
        additional_allowed_dirs=[shared_dir],
    )

    api_get_data_info(
        data_path=data_path.as_posix(),
        config_file=config_path,
    )

    assert fake_data_info.calls[-1]["data_path"] == data_path.resolve()


def test_local_file_outside_working_dir_is_rejected_when_boundary_is_enabled(
    tmp_path,
) -> None:
    working_dir = tmp_path / "work"
    outside_dir = tmp_path / "outside"
    working_dir.mkdir()
    outside_dir.mkdir()
    data_path = outside_dir / "data.csv"
    data_path.write_text("x,y\n1,2\n", encoding="utf-8")
    config_path = _write_config(tmp_path, working_dir, strict_local_boundary=True)

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
    config_path = _write_config(tmp_path, working_dir, strict_local_boundary=True)

    with caplog.at_level(logging.WARNING):
        result = api_get_data_info(
            data_path=data_path.as_posix(),
            config_file=config_path,
        )

    messages = _joined_log_messages(caplog)
    assert result == "Access denied: data file must be within the working directory."
    assert "[SECURITY VIOLATION]" in messages
    assert "resolved_path" not in messages
    assert "requested_path" not in messages
    assert "working_dir" not in messages


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
    config_path = _write_config(tmp_path, working_dir, strict_local_boundary=True)
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


def test_url_guard_disabled_does_not_apply_baseline_url_restrictions(
    monkeypatch,
    tmp_path,
) -> None:
    fake_data_info = _patch_fake_data_info(monkeypatch)
    working_dir = tmp_path / "work"
    working_dir.mkdir()
    config_path = _write_config(tmp_path, working_dir, enable_guard=False)

    for url in (
        "http://example.com/data.csv",
        "https://192.168.1.1/data.csv",
        "https://evil.com@example.com/data.csv",
    ):
        result = api_get_data_info(
            data_path=url,
            config_file=config_path,
        )

        payload = json.loads(result)
        assert payload["overview"]["source"] == url

    assert [call["data_path"] for call in fake_data_info.calls] == [
        "http://example.com/data.csv",
        "https://192.168.1.1/data.csv",
        "https://evil.com@example.com/data.csv",
    ]


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


def test_url_guard_enabled_rejects_http_scheme_logs_security_violation(
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
            data_path="http://example.com/data.csv",
            config_file=config_path,
        )

    messages = _joined_log_messages(caplog)
    assert result == "Access denied: only HTTPS URLs are allowed."
    assert "[SECURITY VIOLATION]" in messages
    assert "non-https-scheme" in messages


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
