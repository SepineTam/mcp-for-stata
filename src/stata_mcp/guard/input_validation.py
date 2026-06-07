"""Validation helpers for values interpolated into Stata commands."""

import re


STATA_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
GITHUB_REPOSITORY_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?/"
    r"[A-Za-z0-9_.-]+$"
)
INSTALL_SOURCES = frozenset({"github", "net", "ssc"})
UNSAFE_STATA_ARGUMENT_PATTERN = re.compile(r"""[\s"'`()`,;$!]""")


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


def validate_net_source_location(location: str | None) -> str | None:
    """Validate a value interpolated into Stata's unquoted ``from(...)``."""
    if location is None:
        return None
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
    return normalized_location


__all__ = [
    "validate_ado_package_name",
    "validate_install_source",
    "validate_net_source_location",
    "validate_stata_identifier",
]
