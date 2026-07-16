#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：DataInfoBase 基类

测试基类的核心功能，不依赖具体文件格式。
"""

import numpy as np
import pandas as pd
import pytest

from stata_mcp.data_info.base import DataInfoBase


class TestIsURL:
    """测试 URL 检测功能"""

    def test_http_url(self):
        """HTTP URL 应该返回 True"""
        assert DataInfoBase._is_url("http://example.com/data.csv") is True

    def test_https_url(self):
        """HTTPS URL 应该返回 True"""
        assert DataInfoBase._is_url("https://example.com/data.csv") is True

    def test_uppercase_url(self):
        """大写 URL 也应该返回 True"""
        assert DataInfoBase._is_url("HTTP://EXAMPLE.COM/DATA.CSV") is True
        assert DataInfoBase._is_url("HTTPS://EXAMPLE.COM/DATA.CSV") is True

    def test_local_absolute_path(self):
        """本地绝对路径应该返回 False"""
        assert DataInfoBase._is_url("/path/to/file.csv") is False
        assert DataInfoBase._is_url("C:\\path\\to\\file.csv") is False

    def test_local_relative_path(self):
        """本地相对路径应该返回 False"""
        assert DataInfoBase._is_url("./relative/path.csv") is False
        assert DataInfoBase._is_url("../parent/path.csv") is False
        assert DataInfoBase._is_url("folder/file.csv") is False

    def test_url_without_scheme(self):
        """没有 scheme 的 URL 应该返回 False"""
        assert DataInfoBase._is_url("example.com/data.csv") is False
        assert DataInfoBase._is_url("www.example.com/data.csv") is False


class TestFileValidation:
    """测试文件验证"""

    def test_file_not_found(self):
        """不存在的文件应该抛出 FileNotFoundError"""
        from stata_mcp.data_info.csv import CsvDataInfo

        with pytest.raises(FileNotFoundError) as exc_info:
            CsvDataInfo("/nonexistent/path/to/file.csv")

        assert "not found" in str(exc_info.value).lower()

    def test_invalid_path_type(self):
        """无效的路径类型应该抛出 TypeError"""
        from stata_mcp.data_info.csv import CsvDataInfo

        with pytest.raises(TypeError):
            CsvDataInfo(12345)  # type: ignore

        with pytest.raises(TypeError):
            CsvDataInfo(None)  # type: ignore

        with pytest.raises(TypeError):
            CsvDataInfo([])  # type: ignore


class TestRuntimeSettings:
    """Test settings passed into a concrete data-info handler."""

    def test_explicit_settings_replace_internal_config_reads(self, tmp_path):
        from stata_mcp.data_info.csv import CsvDataInfo

        data_path = tmp_path / "sample.csv"
        data_path.write_text("value,label\n1,a\n2,b\n", encoding="utf-8")

        data_info = CsvDataInfo(
            data_path,
            is_cache=False,
            metrics=["med", "q1", "med"],
            string_keep_number=2,
            decimal_places=1,
            hash_length=6,
        )

        assert data_info.is_cache is False
        assert data_info.metrics == ["med", "q1"]
        assert data_info.string_keep_number == 2
        assert data_info.decimal_places == 1
        assert data_info.HASH_LENGTH == 6

    def test_invalid_direct_metrics_fall_back_to_legacy_defaults(self, tmp_path):
        from stata_mcp.data_info.csv import CsvDataInfo

        data_path = tmp_path / "sample.csv"
        data_path.write_text("value\n1\n", encoding="utf-8")

        data_info = CsvDataInfo(data_path, metrics=["unsupported"])

        assert data_info.metrics == DataInfoBase.DEFAULT_METRICS

    def test_cache_is_isolated_by_output_settings(self, tmp_path):
        from stata_mcp.data_info.csv import CsvDataInfo

        data_path = tmp_path / "sample.csv"
        cache_dir = tmp_path / "cache"
        data_path.write_text(
            "value,label\n1.1234,alpha\n2.2345,beta\n",
            encoding="utf-8",
        )
        first_handler = CsvDataInfo(
            data_path,
            cache_dir=cache_dir,
            metrics=["mean"],
            string_keep_number=1,
            decimal_places=1,
        )
        second_handler = CsvDataInfo(
            data_path,
            cache_dir=cache_dir,
            metrics=["mean"],
            string_keep_number=2,
            decimal_places=4,
        )
        different_metrics_handler = CsvDataInfo(
            data_path,
            cache_dir=cache_dir,
            metrics=["max"],
            string_keep_number=2,
            decimal_places=4,
        )

        first_result = first_handler.info
        second_result = second_handler.info

        assert first_handler.cached_file != second_handler.cached_file
        assert second_handler.cached_file != different_metrics_handler.cached_file
        assert first_result["vars_detail"]["value"]["summary"]["mean"] == 1.7
        assert second_result["vars_detail"]["value"]["summary"]["mean"] == 1.6789
        assert second_result["vars_detail"]["label"]["summary"]["value_list"] == [
            "alpha",
            "beta",
        ]
        assert second_result["info_config"]["decimal_places"] == 4
        assert len(list(cache_dir.glob("*.json"))) == 2


class TestDetermineVariableType:
    """测试 _determine_variable_type 静态方法"""

    def test_empty_series_returns_float(self):
        """空序列应默认判定为 float"""
        series = pd.Series([], dtype="float64")

        assert DataInfoBase._determine_variable_type(series) == "float"

    def test_all_na_series_returns_float(self):
        """全为 NA 的序列应判定为 float"""
        series = pd.Series([np.nan, np.nan, np.nan])

        assert DataInfoBase._determine_variable_type(series) == "float"

    def test_string_dtype_numeric_returns_float(self):
        """string dtype 且值为数字时应判定为 float"""
        series = pd.Series(["11", "22", "33"], dtype="string")

        assert DataInfoBase._determine_variable_type(series) == "float"

    def test_object_dtype_numeric_returns_float(self):
        """object dtype 且值为数字时应判定为 float"""
        series = pd.Series(["11", "22", "33"], dtype="object")

        assert DataInfoBase._determine_variable_type(series) == "float"

    def test_decimal_strings_returns_float(self):
        """小数数字字符串应判定为 float"""
        series = pd.Series(["1.5", "2.5", "3.5"], dtype="string")

        assert DataInfoBase._determine_variable_type(series) == "float"

    def test_negative_strings_returns_float(self):
        """负数字符串应判定为 float"""
        series = pd.Series(["-1", "-2", "-3"], dtype="string")

        assert DataInfoBase._determine_variable_type(series) == "float"

    def test_mixed_numeric_non_numeric_returns_str(self):
        """混合数字和非数字时应判定为 str"""
        series = pd.Series(["11", "22", "xx"], dtype="string")

        assert DataInfoBase._determine_variable_type(series) == "str"

    def test_non_numeric_strings_returns_str(self):
        """纯文本字符串应判定为 str"""
        series = pd.Series(["A", "B", "C"], dtype="string")

        assert DataInfoBase._determine_variable_type(series) == "str"
