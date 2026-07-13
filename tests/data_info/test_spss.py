#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：SPSS 数据处理器

测试 SPSS 数据处理器对本地文件和 URL 的处理。
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from stata_mcp.data_info.spss import SpssDataInfo


class TestSpssDataInfoURLTimeout:
    """测试 URL 下载时是否传入超时参数"""

    @patch("stata_mcp.data_info.spss.requests.get")
    @patch("stata_mcp.data_info.spss.pyreadstat.read_sav")
    def test_url_fetch_uses_default_timeout(
        self,
        mock_read_sav: MagicMock,
        mock_requests_get: MagicMock,
        tmp_path,
    ) -> None:
        """通过 URL 读取 SPSS 文件时应使用 base 中定义的 DEFAULT_TIMEOUT"""
        mock_response = MagicMock()
        mock_response.content = b"fake spss bytes"
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response

        mock_df = pd.DataFrame({"x": [1, 2, 3]})
        mock_meta = MagicMock()
        mock_meta.column_labels = None
        mock_read_sav.return_value = (mock_df, mock_meta)

        info = SpssDataInfo(
            "https://example.com/data.sav",
            cache_dir=tmp_path,
            is_cache=False,
        )
        _ = info.df

        mock_requests_get.assert_called_once()
        _, kwargs = mock_requests_get.call_args
        assert kwargs.get("timeout") == SpssDataInfo.DEFAULT_TIMEOUT

    @patch("stata_mcp.data_info.spss.requests.get")
    @patch("stata_mcp.data_info.spss.pyreadstat.read_sav")
    def test_url_with_invalid_extension_raises(
        self,
        mock_read_sav: MagicMock,
        mock_requests_get: MagicMock,
        tmp_path,
    ) -> None:
        """URL 后缀不是 .sav 或 .zsav 时应抛出 ValueError"""
        info = SpssDataInfo(
            "https://example.com/data.csv",
            cache_dir=tmp_path,
            is_cache=False,
        )

        with pytest.raises(ValueError, match="must point to an SPSS file"):
            _ = info.df

        mock_requests_get.assert_not_called()
        mock_read_sav.assert_not_called()
