#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : get_data_info.py

import ipaddress
import json
import logging
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from ..data_info import get_data_handler
from ._runtime import create_runtime_context

LOCAL_ACCESS_DENIED = "Access denied: data file must be within the working directory."
URL_DOMAIN_ACCESS_DENIED = "Access denied: URL domain is not in the allowlist."
IP_URL_ACCESS_DENIED = "Access denied: IP-based URLs are not allowed."
NON_HTTPS_URL_ACCESS_DENIED = "Access denied: only HTTPS URLs are allowed."
URL_USERINFO_ACCESS_DENIED = "Access denied: URL userinfo is not allowed."


def _is_url(data_path: str) -> bool:
    parsed_url = urlparse(data_path)
    return bool(parsed_url.scheme and parsed_url.netloc)


def _is_ip_host(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def _is_allowed_domain(host: str, allowed_domains: tuple[str, ...]) -> bool:
    normalized_host = host.rstrip(".").lower()
    for allowed_domain in allowed_domains:
        normalized_allowed = allowed_domain.strip().rstrip(".").lower()
        if not normalized_allowed:
            continue
        if normalized_host == normalized_allowed:
            return True
        if normalized_host.endswith(f".{normalized_allowed}"):
            return True
    return False


def _safe_url_for_log(data_path: str) -> str:
    parsed_url = urlparse(data_path)
    safe_url = parsed_url._replace(query="", fragment="")
    return safe_url.geturl()


def _log_url_security_violation(data_path: str, host: str | None, reason: str) -> None:
    logging.warning(
        "[SECURITY VIOLATION] Attempted to access data URL outside allowlist: "
        f"requested_url='{_safe_url_for_log(data_path)}', "
        f"host='{host}', "
        f"reason='{reason}'"
    )


def _validate_local_path(
    data_path: str,
    working_dir: Path,
    *,
    enforce_boundary: bool,
) -> Path | str:
    candidate_path = Path(data_path).expanduser()
    if not enforce_boundary:
        return candidate_path.resolve()

    if not candidate_path.is_absolute():
        candidate_path = working_dir / candidate_path
    resolved_data_path = candidate_path.resolve()
    resolved_working_dir = working_dir.resolve()
    try:
        resolved_data_path.relative_to(resolved_working_dir)
    except ValueError:
        logging.warning(
            "[SECURITY VIOLATION] Attempted to access data file outside working directory: "
            f"requested_path='{data_path}', "
            f"resolved_path='{resolved_data_path}', "
            f"working_dir='{resolved_working_dir.as_posix()}'"
        )
        return LOCAL_ACCESS_DENIED
    return resolved_data_path


def _validate_url(data_path: str, runtime_config) -> tuple[str, str] | str:
    parsed_url = urlparse(data_path)
    host = parsed_url.hostname
    data_extension = Path(parsed_url.path).suffix.lower().strip(".")
    if not runtime_config.ENABLE_DATA_INFO_URL_GUARD:
        return data_path, data_extension

    if parsed_url.scheme.lower() != "https":
        _log_url_security_violation(data_path, host, "non-https-scheme")
        return NON_HTTPS_URL_ACCESS_DENIED
    if parsed_url.username or parsed_url.password:
        _log_url_security_violation(data_path, host, "url-userinfo-not-allowed")
        return URL_USERINFO_ACCESS_DENIED

    if not host:
        _log_url_security_violation(data_path, host, "domain-not-in-allowlist")
        return URL_DOMAIN_ACCESS_DENIED
    if _is_ip_host(host):
        _log_url_security_violation(data_path, host, "ip-host-not-allowed")
        return IP_URL_ACCESS_DENIED

    if runtime_config.ENABLE_DATA_INFO_URL_GUARD and not _is_allowed_domain(
        host,
        runtime_config.DATA_INFO_ALLOWED_URL_DOMAINS,
    ):
        _log_url_security_violation(data_path, host, "domain-not-in-allowlist")
        return URL_DOMAIN_ACCESS_DENIED

    return data_path, data_extension


def _get_data_info_impl(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    config_file: str | Path | None = None,
    *,
    head: int = 0,
) -> str:
    """Return descriptive statistics for a supported dataset."""
    runtime = create_runtime_context(config_file=config_file)

    if _is_url(data_path):
        validated_data = _validate_url(data_path, runtime.config)
        if not isinstance(validated_data, tuple):
            return validated_data
        resolved_data_path, data_extension = validated_data
    else:
        validated_data_path = _validate_local_path(
            data_path,
            runtime.config.WORKING_DIR,
            enforce_boundary=runtime.config.STRICT_DATA_INFO_LOCAL_BOUNDARY,
        )
        if isinstance(validated_data_path, str):
            return validated_data_path
        resolved_data_path = validated_data_path
        data_extension = resolved_data_path.suffix.lower().strip(".")

    data_info_cls = get_data_handler(data_extension)
    if not data_info_cls:
        logging.warning("Unsupported file extension for data_info: %s", data_extension)
        return f"Unsupported file extension now: {data_extension}"

    data_info = data_info_cls(
        resolved_data_path,
        vars_list,
        encoding=encoding,
        cache_dir=runtime.tmp_base_path,
        head=head,
    )
    try:
        return json.dumps(data_info.info, ensure_ascii=False)
    except Exception as error:
        logging.error(
            "Failed to serialize data summary for %s: %s",
            _safe_url_for_log(str(resolved_data_path)),
            error,
        )
        return f"Failed to generate data summary for {resolved_data_path}: {error}"


def get_data_info(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    config_file: str | Path | None = None,
) -> str:
    """Return descriptive statistics for a supported dataset."""
    return _get_data_info_impl(
        data_path=data_path,
        vars_list=vars_list,
        encoding=encoding,
        config_file=config_file,
    )
