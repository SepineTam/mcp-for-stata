"""Validation helpers for values interpolated into Stata commands."""

import re
from collections.abc import Collection
from ipaddress import ip_address
from urllib.parse import urlsplit


STATA_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
GITHUB_REPOSITORY_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/"
    r"[A-Za-z0-9_.-]+$"
)
INSTALL_SOURCES = frozenset({"github", "net", "ssc"})
UNSAFE_STATA_ARGUMENT_PATTERN = re.compile(r"""[\x00-\x20\x7f-\x9f"'`()`,;$!%\\]""")
SAFE_NET_PATH_PATTERN = re.compile(r"^[A-Za-z0-9._~/-]*$")


def validate_stata_identifier(value: str, *, field_name: str) -> str:
    """Return a normalized Stata identifier or reject unsafe input."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")

    normalized_value = value.strip()
    if not STATA_IDENTIFIER_PATTERN.fullmatch(normalized_value):
        raise ValueError(
            f"Invalid {field_name}. It must start with a letter or underscore "
            "and contain only letters, numbers, and underscores."
        )
    return normalized_value


def validate_install_source(source: str) -> str:
    """Return a supported normalized ado installation source."""
    if not isinstance(source, str):
        raise TypeError("Ado installation source must be a string.")

    normalized_source = source.strip().lower()
    if normalized_source not in INSTALL_SOURCES:
        supported_sources = ", ".join(sorted(INSTALL_SOURCES))
        raise ValueError(
            f"Invalid ado installation source. Supported sources: {supported_sources}."
        )
    return normalized_source


def validate_ado_package_name(package: str, *, source: str) -> str:
    """Validate a package name according to its installation source."""
    normalized_source = validate_install_source(source)
    if normalized_source != "github":
        return validate_stata_identifier(package, field_name="ado package name")

    if not isinstance(package, str):
        raise TypeError("GitHub repository must be a string.")

    normalized_package = package.strip()
    if (
        not GITHUB_REPOSITORY_PATTERN.fullmatch(normalized_package)
        or normalized_package.endswith(".")
        or ".." in normalized_package
    ):
        raise ValueError(
            "Invalid GitHub repository. Expected a safe 'owner/repository' value."
        )
    return normalized_package


def require_ado_install_confirmation(confirmed: bool) -> None:
    """Require an explicit acknowledgement before installing third-party code."""
    if confirmed is not True:
        raise PermissionError(
            "Ado package installation executes third-party code. "
            "Set confirm=True only after the user explicitly approves the "
            "package and source."
        )


def validate_github_repository_allowed(
    repository: str,
    *,
    allowed_repositories: Collection[str] = (),
) -> str:
    """Require a GitHub repository to be explicitly allowlisted."""
    normalized_repository = validate_ado_package_name(repository, source="github")
    normalized_allowlist = {
        str(item).strip().lower()
        for item in allowed_repositories
        if str(item).strip()
    }
    if normalized_repository.lower() not in normalized_allowlist:
        raise PermissionError(
            f"GitHub repository '{normalized_repository}' is not allowlisted. "
            "Configure SECURITY.ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES "
            "before installing."
        )
    return normalized_repository


def validate_ssc_package_allowed(
    package: str,
    *,
    allowed_packages: Collection[str] = (),
) -> str:
    """Require an SSC package to be explicitly allowlisted."""
    normalized_package = validate_ado_package_name(package, source="ssc")
    normalized_allowlist = {
        str(item).strip().lower()
        for item in allowed_packages
        if str(item).strip()
    }
    if normalized_package.lower() not in normalized_allowlist:
        raise PermissionError(
            f"SSC package '{normalized_package}' is not allowlisted. "
            "Configure SECURITY.ADO_INSTALL_ALLOWED_SSC_PACKAGES before installing."
        )
    return normalized_package


def validate_net_source_location(
    location: str | None,
    *,
    allowed_hosts: Collection[str] = (),
    allowed_sources: Collection[str] = (),
) -> str:
    """Validate an allowlisted HTTPS source interpolated into ``from(...)``."""
    if location is None:
        raise ValueError("A net package source location is required.")
    if not isinstance(location, str):
        raise TypeError("Net package source location must be a string.")

    normalized_location = location.strip()
    if (
        not normalized_location
        or UNSAFE_STATA_ARGUMENT_PATTERN.search(normalized_location)
    ):
        raise ValueError(
            "Invalid net package source location. Whitespace, Stata syntax "
            "delimiters, macro markers, and command prefixes are not allowed."
        )

    parsed_location = urlsplit(normalized_location)
    try:
        source_port = parsed_location.port
    except ValueError as error:
        raise ValueError(
            "Invalid net package source location. The URL port is invalid."
        ) from error
    if (
        parsed_location.scheme.lower() != "https"
        or not parsed_location.hostname
        or parsed_location.username is not None
        or parsed_location.password is not None
        or parsed_location.query
        or parsed_location.fragment
        or source_port not in {None, 443}
        or not parsed_location.hostname.isascii()
        or not SAFE_NET_PATH_PATTERN.fullmatch(parsed_location.path)
        or "//" in parsed_location.path
        or any(
            segment in {".", ".."}
            for segment in parsed_location.path.split("/")
        )
    ):
        raise ValueError(
            "Invalid net package source location. Only HTTPS URLs without "
            "credentials, query strings, fragments, non-default ports, or "
            "unsafe path characters are allowed."
        )

    normalized_hosts = {
        str(host).strip().lower().rstrip(".")
        for host in allowed_hosts
        if str(host).strip()
    }
    source_host = parsed_location.hostname.lower().rstrip(".")
    try:
        ip_address(source_host)
    except ValueError:
        pass
    else:
        raise ValueError(
            "Invalid net package source location. IP-address hosts are not allowed."
        )

    if source_host not in normalized_hosts:
        raise PermissionError(
            f"Net package source host '{source_host}' is not allowlisted. "
            "Configure SECURITY.ADO_INSTALL_ALLOWED_NET_HOSTS before installing."
        )

    normalized_sources = {
        str(source).strip()
        for source in allowed_sources
        if str(source).strip()
    }
    if normalized_location not in normalized_sources:
        raise PermissionError(
            f"Net package source '{normalized_location}' is not allowlisted. "
            "Configure SECURITY.ADO_INSTALL_ALLOWED_NET_SOURCES before installing."
        )
    return normalized_location


def validate_ado_install_request(
    package: str,
    source: str,
    package_source_from: str | None,
    *,
    allowed_github_repositories: Collection[str] = (),
    allowed_net_hosts: Collection[str] = (),
    allowed_net_sources: Collection[str] = (),
    allowed_ssc_packages: Collection[str] = (),
) -> tuple[str, str, str | None]:
    """Validate and normalize a complete ado installation request."""
    normalized_source = validate_install_source(source)
    if normalized_source == "github":
        normalized_package = validate_github_repository_allowed(
            package,
            allowed_repositories=allowed_github_repositories,
        )
    elif normalized_source == "ssc":
        normalized_package = validate_ssc_package_allowed(
            package,
            allowed_packages=allowed_ssc_packages,
        )
    else:
        normalized_package = validate_ado_package_name(
            package,
            source=normalized_source,
        )

    if normalized_source == "net":
        normalized_location = validate_net_source_location(
            package_source_from,
            allowed_hosts=allowed_net_hosts,
            allowed_sources=allowed_net_sources,
        )
    elif package_source_from is not None:
        raise ValueError("package_source_from is only valid when source='net'.")
    else:
        normalized_location = None

    return normalized_package, normalized_source, normalized_location


__all__ = [
    "validate_ado_package_name",
    "validate_ado_install_request",
    "validate_github_repository_allowed",
    "validate_install_source",
    "validate_net_source_location",
    "validate_ssc_package_allowed",
    "validate_stata_identifier",
    "require_ado_install_confirmation",
]
