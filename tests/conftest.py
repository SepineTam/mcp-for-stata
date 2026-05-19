#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局 pytest fixtures。

这个文件定义了所有测试共享的 fixtures。
pytest 会自动发现这个文件中的 fixtures。
"""

import urllib.request
from pathlib import Path

import pytest

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "fixtures" / "dataset"
STATA_BASE_URL = "https://www.stata-press.com/data/r17"


def _download_dta(name: str) -> Path | None:
    """Download a single .dta dataset from Stata Press."""
    dest = TEST_DATA_DIR / f"{name}.dta"
    if dest.exists():
        return dest

    url = f"{STATA_BASE_URL}/{name}.dta"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.read())
        return dest
    except Exception:
        if dest.exists():
            dest.unlink()
        return None


def _ensure_auto_fixtures() -> bool:
    """Download auto.dta and generate CSV/XLSX/SAV from it."""
    dta_path = _download_dta("auto")
    if dta_path is None:
        return False

    csv_path = TEST_DATA_DIR / "auto.csv"
    xlsx_path = TEST_DATA_DIR / "auto.xlsx"
    sav_path = TEST_DATA_DIR / "auto.sav"

    if csv_path.exists() and xlsx_path.exists() and sav_path.exists():
        return True

    import pandas as pd

    df = pd.read_stata(dta_path)  # type: ignore[assignment]

    if not csv_path.exists():
        df.to_csv(csv_path, index=False)  # type: ignore[union-attr]

    if not xlsx_path.exists():
        df.to_excel(xlsx_path, index=False, engine="openpyxl")  # type: ignore[union-attr]

    if not sav_path.exists():
        import pyreadstat

        pyreadstat.write_sav(df, str(sav_path))  # type: ignore[arg-type]

    return True


def _ensure_fixtures():
    """运行时拉取 fixture 数据（如果不存在）。"""
    if not _ensure_auto_fixtures():
        pytest.skip("Failed to download fixture data from Stata Press")


# ============ 路径 Fixtures ============

@pytest.fixture
def sample_csv_path():
    """CSV 测试文件路径"""
    _ensure_fixtures()
    path = TEST_DATA_DIR / "auto.csv"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


@pytest.fixture
def sample_xlsx_path():
    """Excel 测试文件路径"""
    _ensure_fixtures()
    path = TEST_DATA_DIR / "auto.xlsx"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


@pytest.fixture
def sample_dta_path():
    """Stata DTA 测试文件路径"""
    _ensure_fixtures()
    path = TEST_DATA_DIR / "auto.dta"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


@pytest.fixture
def sample_sav_path():
    """SPSS SAV 测试文件路径"""
    _ensure_fixtures()
    path = TEST_DATA_DIR / "auto.sav"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


# ============ 数据 Fixtures ============

@pytest.fixture
def sample_csv_data(sample_csv_path):
    """CSV 文件的数据内容"""
    from stata_mcp.data_info.csv import CsvDataInfo
    return CsvDataInfo(sample_csv_path)


@pytest.fixture
def sample_dta_data(sample_dta_path):
    """DTA 文件的数据内容"""
    from stata_mcp.data_info.dta import DtaDataInfo
    return DtaDataInfo(sample_dta_path)


@pytest.fixture
def sample_xlsx_data(sample_xlsx_path):
    """Excel 文件的数据内容"""
    from stata_mcp.data_info.xlsx import ExcelDataInfo
    return ExcelDataInfo(sample_xlsx_path)
