#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：DataInfoBase 基类

测试基类的核心功能，不依赖具体文件格式。
"""

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
