#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：ExcelDataInfo 类

测试 Excel 文件读取功能。
"""

import pytest

from stata_mcp.data_info.xlsx import ExcelDataInfo


class TestXlsxReading:
    """测试 Excel 文件读取"""

    def test_df_not_none(self, sample_xlsx_data):
        """df 属性应该返回 DataFrame"""
        df = sample_xlsx_data.df
        assert df is not None

    def test_df_shape(self, sample_xlsx_data):
        """测试 DataFrame 的形状"""
        df = sample_xlsx_data.df
        assert len(df) == 74
        assert len(df.columns) == 12

    def test_df_columns(self, sample_xlsx_data):
        """测试 DataFrame 的列名"""
        df = sample_xlsx_data.df
        expected_cols = ["make", "price", "mpg", "rep78", "headroom",
                         "trunk", "weight", "length", "turn",
                         "displacement", "gear_ratio", "foreign"]
        assert list(df.columns) == expected_cols


class TestXlsxSummary:
    """测试 Excel 数据摘要"""

    def test_summary_overview(self, sample_xlsx_data):
        """测试 overview 部分"""
        summary = sample_xlsx_data.summary()

        assert "overview" in summary
        assert summary["overview"]["obs"] == 74
        assert summary["overview"]["var_numbers"] == 12

    def test_summary_vars_detail(self, sample_xlsx_data):
        """测试 vars_detail 部分"""
        summary = sample_xlsx_data.summary()

        assert "vars_detail" in summary
        assert "make" in summary["vars_detail"]
        assert "price" in summary["vars_detail"]
