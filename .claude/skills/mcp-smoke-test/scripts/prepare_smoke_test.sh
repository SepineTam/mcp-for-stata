#!/usr/bin/env bash
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : .claude/skills/mcp-smoke-test/scripts/prepare_smoke_test.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../../../" && pwd)"
SKILL_DIR="${PROJECT_ROOT}/.claude/skills/mcp-smoke-test"

echo "Project root: ${PROJECT_ROOT}"

# Ensure a fresh cache directory for get_data_info.
CACHE_DIR="${PROJECT_ROOT}/.statamcp/stata-mcp-tmp"
if [[ -d "${CACHE_DIR}" ]]; then
    echo "Clearing cached data_info summaries..."
    rm -rf "${CACHE_DIR}/data_info__"*
fi

# Locate a usable auto.dta, preferring the real Stata samples.
AUTO_DTA=""
for candidate in \
    "/Applications/Stata/auto.dta" \
    "/Applications/StataNow/auto.dta" \
    "${PROJECT_ROOT}/tests/fixtures/dataset/auto.dta"; do
    if [[ -f "${candidate}" ]]; then
        AUTO_DTA="${candidate}"
        echo "Found auto.dta: ${AUTO_DTA}"
        break
    fi
done

if [[ -z "${AUTO_DTA}" ]]; then
    echo "No system auto.dta found; generating mock data..."
    cd "${PROJECT_ROOT}"
    uv run "${SKILL_DIR}/scripts/gen_mock_data.py" --output-dir "${PROJECT_ROOT}/tmp" --name auto_mock
    AUTO_DTA="${PROJECT_ROOT}/tmp/auto_mock.dta"
fi

# Copy data and boundary dofile to /tmp for the security boundary test.
echo "Copying test artifacts to /tmp..."
cp "${AUTO_DTA}" /tmp/auto.dta
cp "${SKILL_DIR}/scripts/boundary.do" /tmp/mcp_smoke_test_boundary.do

echo "Smoke test preparation complete."
