#!/usr/bin/env bash
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : .claude/skills/mcp-smoke-test/scripts/cleanup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../../" && pwd)"

echo "Cleaning up smoke test artifacts..."

# Remove files copied to /tmp for the security boundary test.
rm -f /tmp/mcp_smoke_test_boundary.do
rm -f /tmp/auto.dta

# Remove mock data generated when no system auto.dta was available.
rm -f "${PROJECT_ROOT}/tmp/auto_mock.dta"
rm -f "${PROJECT_ROOT}/tmp/auto_mock.csv"

# Clear cached get_data_info summaries.
CACHE_DIR="${PROJECT_ROOT}/.statamcp/stata-mcp-tmp"
if [[ -d "${CACHE_DIR}" ]]; then
    rm -rf "${CACHE_DIR}/data_info__"*
fi

echo "Cleanup complete."
