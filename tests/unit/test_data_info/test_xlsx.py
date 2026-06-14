#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：ExcelDataInfo 类

测试 Excel 文件读取功能。
"""

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


class TestXlsxStringNumericColumn:
    """测试 Excel 中字符串类型但内容为数值的列"""

    def test_string_dtype_numeric_values_summary(self, tmp_path):
        """string dtype 且值为数字时应按 float 计算摘要"""
        import pandas as pd

        xlsx_path = tmp_path / "string_numeric.xlsx"
        df = pd.DataFrame({
            "code": pd.Series(["11", "22", "33", "44", "55"], dtype="string"),
        })
        df.to_excel(xlsx_path, index=False, engine="openpyxl")

        data_info = ExcelDataInfo(xlsx_path, dtype={"code": "string"})
        summary = data_info.summary()

        code_info = summary["vars_detail"]["code"]
        assert code_info["type"] == "float"
        assert code_info["summary"]["mean"] == 33.0

    def test_mixed_numeric_and_text_strings_summary(self, tmp_path):
        """混合数字和文本的字符串列应保持为 str"""
        import pandas as pd

        xlsx_path = tmp_path / "mixed.xlsx"
        df = pd.DataFrame({
            "code": pd.Series(["11", "22", "xx", "44", "55"], dtype="string"),
        })
        df.to_excel(xlsx_path, index=False, engine="openpyxl")

        data_info = ExcelDataInfo(xlsx_path, dtype={"code": "string"})
        summary = data_info.summary()

        code_info = summary["vars_detail"]["code"]
        assert code_info["type"] == "str"
        assert "value_list" in code_info["summary"]
