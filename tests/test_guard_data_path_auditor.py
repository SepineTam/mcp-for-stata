"""Tests for the shared DataPathAuditor."""

import logging
from pathlib import Path

import pytest

from stata_mcp.guard.data_path_auditor import (
    IP_URL_ACCESS_DENIED,
    LOCAL_ACCESS_DENIED,
    NON_HTTPS_URL_ACCESS_DENIED,
    URL_DOMAIN_ACCESS_DENIED,
    URL_USERINFO_ACCESS_DENIED,
    DataPathAuditor,
)


@pytest.fixture
def working_dir(tmp_path: Path) -> Path:
    work = tmp_path / "work"
    work.mkdir()
    return work


@pytest.fixture
def auditor(working_dir: Path) -> DataPathAuditor:
    return DataPathAuditor(
        working_dir=working_dir,
        strict_local_boundary=True,
        enable_url_guard=True,
        allowed_url_domains=("example.com",),
    )


def test_local_file_within_working_dir_is_allowed(
    auditor: DataPathAuditor, working_dir: Path
) -> None:
    data_file = working_dir / "data.csv"
    data_file.write_text("x,y\n1,2\n", encoding="utf-8")

    result = auditor.validate_local_path(data_file.as_posix())

    assert isinstance(result, Path)
    assert result == data_file.resolve()


def test_local_file_outside_working_dir_is_rejected(
    auditor: DataPathAuditor, tmp_path: Path
) -> None:
    outside_file = tmp_path / "outside.csv"
    outside_file.write_text("x,y\n1,2\n", encoding="utf-8")

    result = auditor.validate_local_path(outside_file.as_posix())

    assert result == LOCAL_ACCESS_DENIED


def test_relative_local_file_resolved_from_working_dir(
    auditor: DataPathAuditor, working_dir: Path
) -> None:
    data_file = working_dir / "data.csv"
    data_file.write_text("x,y\n1,2\n", encoding="utf-8")

    result = auditor.validate_local_path("data.csv")

    assert isinstance(result, Path)
    assert result == data_file.resolve()


def test_relative_local_file_escaping_working_dir_is_rejected(
    auditor: DataPathAuditor,
) -> None:
    result = auditor.validate_local_path("../outside.csv")

    assert result == LOCAL_ACCESS_DENIED


def test_local_boundary_disabled_allows_outside_path(
    auditor: DataPathAuditor, tmp_path: Path
) -> None:
    permissive_auditor = DataPathAuditor(
        working_dir=auditor.working_dir,
        strict_local_boundary=False,
        enable_url_guard=True,
        allowed_url_domains=(),
    )
    outside_file = tmp_path / "outside.csv"
    outside_file.write_text("x,y\n1,2\n", encoding="utf-8")

    result = permissive_auditor.validate_local_path(outside_file.as_posix())

    assert isinstance(result, Path)
    assert result == outside_file.resolve()


def test_https_allowlisted_domain_is_allowed(auditor: DataPathAuditor) -> None:
    result = auditor.validate_url("https://example.com/data.csv")

    assert isinstance(result, tuple)
    assert result == ("https://example.com/data.csv", "csv")


def test_subdomain_of_allowlisted_domain_is_allowed(auditor: DataPathAuditor) -> None:
    result = auditor.validate_url("https://sub.example.com/data.csv")

    assert isinstance(result, tuple)
    assert result[0] == "https://sub.example.com/data.csv"


def test_non_allowlisted_domain_is_rejected(auditor: DataPathAuditor) -> None:
    result = auditor.validate_url("https://evil.com/data.csv")

    assert result == URL_DOMAIN_ACCESS_DENIED


def test_http_scheme_is_rejected(auditor: DataPathAuditor) -> None:
    result = auditor.validate_url("http://example.com/data.csv")

    assert result == NON_HTTPS_URL_ACCESS_DENIED


def test_ip_host_is_rejected(auditor: DataPathAuditor) -> None:
    result = auditor.validate_url("https://192.168.1.1/data.csv")

    assert result == IP_URL_ACCESS_DENIED


def test_url_with_userinfo_is_rejected(auditor: DataPathAuditor) -> None:
    result = auditor.validate_url("https://user:pass@example.com/data.csv")

    assert result == URL_USERINFO_ACCESS_DENIED


def test_url_guard_disabled_allows_any_url(auditor: DataPathAuditor) -> None:
    permissive_auditor = DataPathAuditor(
        working_dir=auditor.working_dir,
        strict_local_boundary=True,
        enable_url_guard=False,
        allowed_url_domains=(),
    )

    result = permissive_auditor.validate_url("http://evil.com/data.csv")

    assert isinstance(result, tuple)
    assert result[0] == "http://evil.com/data.csv"


def test_url_log_redacts_query_and_fragment(caplog, auditor: DataPathAuditor) -> None:
    with caplog.at_level(logging.WARNING):
        auditor.validate_url("https://evil.com/data.csv?token=secret#anchor")

    messages = "\n".join(caplog.messages)
    assert "requested_url='https://evil.com/data.csv'" in messages
    assert "token=secret" not in messages
    assert "#anchor" not in messages


def test_url_log_redacts_userinfo(caplog, auditor: DataPathAuditor) -> None:
    with caplog.at_level(logging.WARNING):
        auditor.validate_url("https://user:pass@evil.com/data.csv?token=secret#anchor")

    messages = "\n".join(caplog.messages)
    assert "requested_url='https://evil.com/data.csv'" in messages
    assert "user:pass@" not in messages
    assert "token=secret" not in messages
    assert "#anchor" not in messages


def test_local_path_log_does_not_include_full_paths(
    caplog, auditor: DataPathAuditor
) -> None:
    with caplog.at_level(logging.WARNING):
        auditor.validate_local_path("../outside.csv")

    messages = "\n".join(caplog.messages)
    assert "[SECURITY VIOLATION]" in messages
    assert "requested_path" not in messages
    assert "resolved_path" not in messages
    assert "working_dir" not in messages
    assert "outside.csv" not in messages
