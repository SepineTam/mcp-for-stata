#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：CsvDataInfo 类

测试 CSV 文件读取功能。
"""

import pytest

from stata_mcp.data_info.csv import CsvDataInfo


class TestCsvReading:
    """测试 CSV 文件读取"""

    def test_df_not_none(self, sample_csv_data):
        """df 属性应该返回 DataFrame"""
        df = sample_csv_data.df
        assert df is not None

    def test_df_shape(self, sample_csv_data):
        """测试 DataFrame 的形状"""
        df = sample_csv_data.df
        assert len(df) == 74  # auto 数据集有 74 行
        assert len(df.columns) == 12  # 12 列

    def test_df_columns(self, sample_csv_data):
        """测试 DataFrame 的列名"""
        df = sample_csv_data.df
        expected_cols = [
            "make", "price", "mpg", "rep78", "headroom",
            "trunk", "weight", "length", "turn",
            "displacement", "gear_ratio", "foreign"
        ]
        assert list(df.columns) == expected_cols

    def test_first_row_data(self, sample_csv_data):
        """测试第一行数据"""
        df = sample_csv_data.df
        first_row = df.iloc[0]
        assert first_row["make"] == "AMC Concord"
        assert first_row["price"] == 4099


class TestCsvSummary:
    """测试 CSV 数据摘要"""

    def test_summary_returns_dict(self, sample_csv_data):
        """summary() 应该返回字典"""
        summary = sample_csv_data.summary()
        assert isinstance(summary, dict)

    def test_summary_has_overview(self, sample_csv_data):
        """summary 应该包含 overview"""
        summary = sample_csv_data.summary()
        assert "overview" in summary

    def test_overview_content(self, sample_csv_data):
        """测试 overview 的内容"""
        summary = sample_csv_data.summary()
        overview = summary["overview"]

        assert overview["obs"] == 74
        assert overview["var_numbers"] == 12
        assert "source" in overview
        assert "hash" in overview

    def test_summary_has_info_config(self, sample_csv_data):
        """summary 应该包含 info_config"""
        summary = sample_csv_data.summary()
        assert "info_config" in summary

    def test_summary_has_vars_detail(self, sample_csv_data):
        """summary 应该包含 vars_detail"""
        summary = sample_csv_data.summary()
        assert "vars_detail" in summary
        assert "make" in summary["vars_detail"]
        assert "price" in summary["vars_detail"]


class TestCsvVarSelection:
    """测试变量选择"""

    def test_vars_list_in_summary(self, sample_csv_path):
        """vars_list 应该在 summary 中生效"""
        data_info = CsvDataInfo(sample_csv_path, vars_list=["make", "price", "mpg"])
        info = data_info.info

        assert len(info["overview"]["var_list"]) == 3
        assert set(info["overview"]["var_list"]) == {"make", "price", "mpg"}

    def test_df_returns_all_columns(self, sample_csv_path):
        """df 属性应该返回所有列，不受 vars_list 影响"""
        data_info = CsvDataInfo(sample_csv_path, vars_list=["make", "price"])
        df = data_info.df

        # df 返回完整数据
        assert len(df.columns) == 12

    def test_single_var_selection(self, sample_csv_path):
        """测试选择单个变量"""
        data_info = CsvDataInfo(sample_csv_path, vars_list="price")
        info = data_info.info

        assert info["overview"]["var_numbers"] == 1
        assert info["overview"]["var_list"] == ["price"]
