#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : guard/data_path_auditor.py

"""Shared data path/URL security auditor."""

import ipaddress
import logging
from pathlib import Path
from urllib.parse import urlparse

LOCAL_ACCESS_DENIED = "Access denied: data file must be within the working directory."
URL_DOMAIN_ACCESS_DENIED = "Access denied: URL domain is not in the allowlist."
IP_URL_ACCESS_DENIED = "Access denied: IP-based URLs are not allowed."
NON_HTTPS_URL_ACCESS_DENIED = "Access denied: only HTTPS URLs are allowed."
URL_USERINFO_ACCESS_DENIED = "Access denied: URL userinfo is not allowed."


class DataPathAuditor:
    """Validate data file paths and URLs against security policy.

    This class centralizes the boundary and URL guard logic used by
    ``get_data_info`` and ``GuardValidator`` so both paths enforce the
    same rules.
    """

    def __init__(
        self,
        working_dir: Path,
        strict_local_boundary: bool,
        enable_url_guard: bool,
        allowed_url_domains: tuple[str, ...],
        additional_allowed_dirs: tuple[Path, ...] = (),
    ) -> None:
        """Initialize the auditor.

        Args:
            working_dir: Base directory for relative local paths.
            strict_local_boundary: When True, reject local paths outside
                ``working_dir``.
            enable_url_guard: When True, enforce HTTPS, host, and allowlist
                restrictions on URLs.
            allowed_url_domains: Domains permitted when URL guard is enabled.
            additional_allowed_dirs: Extra roots accepted by strict local
                boundary checks.
        """
        self.working_dir = working_dir
        self.strict_local_boundary = strict_local_boundary
        self.enable_url_guard = enable_url_guard
        self.allowed_url_domains = allowed_url_domains
        self.additional_allowed_dirs = additional_allowed_dirs

    @staticmethod
    def is_url(data_path: str) -> bool:
        """Return True when ``data_path`` looks like a URL."""
        parsed_url = urlparse(data_path)
        return bool(parsed_url.scheme and parsed_url.netloc)

    @staticmethod
    def _is_ip_host(host: str) -> bool:
        """Return True when ``host`` is an IP address literal."""
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return False
        return True

    @staticmethod
    def _is_allowed_domain(host: str, allowed_domains: tuple[str, ...]) -> bool:
        """Return True when ``host`` matches an allowed domain."""
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

    @staticmethod
    def _safe_url_for_log(data_path: str) -> str:
        """Return ``data_path`` with userinfo, query, and fragment redacted."""
        parsed_url = urlparse(data_path)
        safe_url = parsed_url._replace(
            netloc=parsed_url.hostname or "",
            query="",
            fragment="",
        )
        return safe_url.geturl()

    @classmethod
    def _log_url_security_violation(
        cls,
        data_path: str,
        host: str | None,
        reason: str,
    ) -> None:
        """Log a URL guard rejection."""
        logging.warning(
            "[SECURITY VIOLATION] Attempted to access data URL outside allowlist: "
            f"requested_url='{cls._safe_url_for_log(data_path)}', "
            f"host='{host}', "
            f"reason='{reason}'"
        )

    def validate_local_path(self, data_path: str) -> Path | str:
        """Validate a local file path.

        Returns the resolved ``Path`` when allowed, or an access-denied
        message string when rejected.
        """
        candidate_path = Path(data_path).expanduser()
        if not self.strict_local_boundary:
            return candidate_path.resolve()

        if not candidate_path.is_absolute():
            candidate_path = self.working_dir / candidate_path
        resolved_data_path = candidate_path.resolve()
        allowed_dirs = (self.working_dir, *self.additional_allowed_dirs)
        for allowed_dir in allowed_dirs:
            try:
                resolved_data_path.relative_to(allowed_dir.resolve())
                return resolved_data_path
            except ValueError:
                continue
        logging.warning(
            "[SECURITY VIOLATION] Attempted to access data file outside allowed directories."
        )
        return LOCAL_ACCESS_DENIED

    def validate_url(self, data_path: str) -> tuple[str, str] | str:
        """Validate a URL.

        Returns a ``(url, extension)`` tuple when allowed, or an
        access-denied message string when rejected.
        """
        parsed_url = urlparse(data_path)
        host = parsed_url.hostname
        data_extension = Path(parsed_url.path).suffix.lower().strip(".")
        if not self.enable_url_guard:
            return data_path, data_extension

        if parsed_url.scheme.lower() != "https":
            self._log_url_security_violation(data_path, host, "non-https-scheme")
            return NON_HTTPS_URL_ACCESS_DENIED
        if parsed_url.username or parsed_url.password:
            self._log_url_security_violation(
                data_path, host, "url-userinfo-not-allowed"
            )
            return URL_USERINFO_ACCESS_DENIED

        if not host:
            self._log_url_security_violation(data_path, host, "domain-not-in-allowlist")
            return URL_DOMAIN_ACCESS_DENIED
        if self._is_ip_host(host):
            self._log_url_security_violation(data_path, host, "ip-host-not-allowed")
            return IP_URL_ACCESS_DENIED

        if not self._is_allowed_domain(host, self.allowed_url_domains):
            self._log_url_security_violation(data_path, host, "domain-not-in-allowlist")
            return URL_DOMAIN_ACCESS_DENIED

        return data_path, data_extension


__all__ = [
    "DataPathAuditor",
    "LOCAL_ACCESS_DENIED",
    "URL_DOMAIN_ACCESS_DENIED",
    "IP_URL_ACCESS_DENIED",
    "NON_HTTPS_URL_ACCESS_DENIED",
    "URL_USERINFO_ACCESS_DENIED",
]
