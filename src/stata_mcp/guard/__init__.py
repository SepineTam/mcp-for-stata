#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : __init__.py

"""Security guard module for Stata MCP.

This module provides security validation for Stata dofiles to prevent
execution of dangerous commands and patterns.

Usage:
    >>> from stata_mcp.guard import GuardValidator
    >>> validator = GuardValidator()
    >>> report = validator.validate(dofile_code)
    >>> if not report.is_safe:
    ...     print(f"Dangerous items found: {report.dangerous_items}")
"""

from .data_path_auditor import DataPathAuditor
from .input_validation import (
    require_ado_install_confirmation,
    validate_ado_install_request,
    validate_ado_package_name,
    validate_github_repository_allowed,
    validate_install_source,
    validate_net_source_location,
    validate_stata_identifier,
)
from .validator import (
    GuardValidator,
    PackageManagementGuardValidator,
    RiskItem,
    SecurityReport,
)

__all__ = [
    "DataPathAuditor",
    "GuardValidator",
    "PackageManagementGuardValidator",
    "RiskItem",
    "SecurityReport",
    "require_ado_install_confirmation",
    "validate_ado_package_name",
    "validate_ado_install_request",
    "validate_github_repository_allowed",
    "validate_install_source",
    "validate_net_source_location",
    "validate_stata_identifier",
]
