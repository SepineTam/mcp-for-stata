#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：DtaDataInfo 类

测试 Stata DTA 文件读取功能。
"""

from stata_mcp.data_info.dta import DtaDataInfo


class TestDtaReading:
    """测试 DTA 文件读取"""

    def test_df_not_none(self, sample_dta_data):
        """df 属性应该返回 DataFrame"""
        df = sample_dta_data.df
        assert df is not None

    def test_df_shape(self, sample_dta_data):
        """测试 DataFrame 的形状"""
        df = sample_dta_data.df
        assert len(df) == 74
        assert len(df.columns) == 12

    def test_df_columns(self, sample_dta_data):
        """测试 DataFrame 的列名"""
        df = sample_dta_data.df
        expected_cols = ["make", "price", "mpg", "rep78", "headroom",
                         "trunk", "weight", "length", "turn",
                         "displacement", "gear_ratio", "foreign"]
        assert list(df.columns) == expected_cols


class TestDtaVariableLabels:
    """测试变量标签读取"""

    def test_has_variable_labels(self, sample_dta_data):
        """DTA 文件应该有变量标签"""
        # 触发读取
        sample_dta_data.df

        # 检查是否有标签
        assert len(sample_dta_data._variable_labels) > 0

    def test_variable_label_in_summary(self, sample_dta_data):
        """变量标签应该出现在 summary 中"""
        summary = sample_dta_data.summary()
        vars_detail = summary["vars_detail"]

        # 检查至少有一个变量有 label
        has_label = False
        for var_info in vars_detail.values():
            if "label" in var_info and var_info["label"]:
                has_label = True
                break

        assert has_label, "At least one variable should have a label"


class TestDtaSummary:
    """测试 DTA 数据摘要"""

    def test_summary_overview(self, sample_dta_data):
        """测试 overview 部分"""
        summary = sample_dta_data.summary()

        assert "overview" in summary
        assert summary["overview"]["obs"] == 74
        assert summary["overview"]["var_numbers"] == 12

    def test_summary_vars_detail(self, sample_dta_data):
        """测试 vars_detail 部分"""
        summary = sample_dta_data.summary()

        assert "vars_detail" in summary
        assert "make" in summary["vars_detail"]
        assert "price" in summary["vars_detail"]

    def test_numeric_var_summary(self, sample_dta_data):
        """测试数值变量的摘要统计"""
        summary = sample_dta_data.summary()
        price_info = summary["vars_detail"]["price"]

        assert price_info["type"] == "float"
        assert "mean" in price_info["summary"]
        assert "min" in price_info["summary"]
        assert "max" in price_info["summary"]

    def test_string_var_summary(self, sample_dta_data):
        """测试字符串变量的摘要统计"""
        summary = sample_dta_data.summary()
        make_info = summary["vars_detail"]["make"]

        assert make_info["type"] == "str"
        assert "obs" in make_info["summary"]


class TestDtaStringNumericColumn:
    """测试字符串类型但内容为数值的列"""

    def test_string_dtype_numeric_values_summary(self, tmp_path):
        """string dtype 且值为数字时应按 float 计算摘要"""
        import pandas as pd

        dta_path = tmp_path / "string_numeric.dta"
        df = pd.DataFrame({
            "code": pd.Series(["11", "22", "33", "44", "55"], dtype="string"),
        })
        df.to_stata(dta_path, write_index=False)

        data_info = DtaDataInfo(dta_path)
        summary = data_info.summary()

        code_info = summary["vars_detail"]["code"]
        assert code_info["type"] == "float"
        assert code_info["summary"]["mean"] == 33.0

    def test_object_dtype_numeric_values_summary(self, tmp_path):
        """object dtype 且值为数字时应按 float 计算摘要"""
        import pandas as pd

        dta_path = tmp_path / "object_numeric.dta"
        df = pd.DataFrame({
            "code": pd.Series(["11", "22", "33", "44", "55"], dtype="object"),
        })
        df.to_stata(dta_path, write_index=False)

        data_info = DtaDataInfo(dta_path)
        summary = data_info.summary()

        code_info = summary["vars_detail"]["code"]
        assert code_info["type"] == "float"
        assert code_info["summary"]["mean"] == 33.0

    def test_mixed_numeric_and_text_strings_summary(self, tmp_path):
        """混合数字和文本的字符串列应保持为 str"""
        import pandas as pd

        dta_path = tmp_path / "mixed.dta"
        df = pd.DataFrame({
            "code": pd.Series(["11", "22", "xx", "44", "55"], dtype="string"),
        })
        df.to_stata(dta_path, write_index=False)

        data_info = DtaDataInfo(dta_path)
        summary = data_info.summary()

        code_info = summary["vars_detail"]["code"]
        assert code_info["type"] == "str"
        assert "value_list" in code_info["summary"]

    def test_actual_string_column_summary(self, tmp_path):
        """普通字符串列应保持为 str"""
        import pandas as pd

        dta_path = tmp_path / "actual_string.dta"
        df = pd.DataFrame({
            "name": ["A", "B", "C", "D", "E"],
        })
        df.to_stata(dta_path, write_index=False)

        data_info = DtaDataInfo(dta_path)
        summary = data_info.summary()

        name_info = summary["vars_detail"]["name"]
        assert name_info["type"] == "str"
        assert "value_list" in name_info["summary"]
