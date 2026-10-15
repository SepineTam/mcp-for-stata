"""Boolean summaries must retain their type and preserve source values."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stata_mcp.data_info import get_data_handler
from stata_mcp.data_info.base import DataInfoBase


@pytest.fixture
def handler_options(tmp_path):
    return {
        "cache_dir": tmp_path / "cache",
        "string_keep_number": 10,
        "decimal_places": 3,
        "hash_length": 12,
        "metrics": ["q1", "med", "q3", "skewness", "kurtosis"],
    }


@pytest.mark.parametrize("suffix", ["csv", "xlsx"])
@pytest.mark.parametrize("is_cache", [False, True])
def test_boolean_file_summary_preserves_source_and_preview(
    tmp_path, monkeypatch, handler_options, suffix, is_cache
):
    data_path = tmp_path / f"sample.{suffix}"
    data = pd.DataFrame({
        "x": [1.2, 2.4, 3.6, 4.8, 5.0],
        "flag": [True, False, True, False, True],
        "binary": [1, 0, 1, 0, 1],
        "label": ["a", "b", "a", "b", "a"],
    })
    if suffix == "csv":
        data.to_csv(data_path, index=False)
    else:
        data.to_excel(data_path, index=False, engine="openpyxl")
    source_bytes = data_path.read_bytes()
    handler_class = get_data_handler(suffix)
    handler = handler_class(
        data_path, is_cache=is_cache, head=5, **handler_options
    )
    original_frame = handler.df.copy(deep=True)

    result = handler.info

    details = result["vars_detail"]
    assert details["flag"]["type"] == "bool"
    assert details["flag"]["summary"] == {
        "obs": 5,
        "mean": 0.6,
        "stderr": 0.245,
        "min": 0.0,
        "max": 1.0,
        "q1": 0.0,
        "med": 1.0,
        "q3": 1.0,
        "skewness": -0.609,
        "kurtosis": -3.333,
    }
    assert details["x"]["type"] == "float"
    assert details["binary"]["type"] == "float"
    assert details["label"]["type"] == "str"
    assert [row["flag"] for row in result["head"]] == data["flag"].tolist()
    assert all(type(row["flag"]) is bool for row in result["head"])
    assert json.loads(json.dumps(result, allow_nan=False))["head"][0]["flag"] is True
    pd.testing.assert_frame_equal(handler.df, original_frame)
    assert data_path.read_bytes() == source_bytes

    if is_cache:
        cache_document = json.loads(handler.cached_file.read_text(encoding="utf-8"))
        assert cache_document["vars_detail"]["flag"]["type"] == "bool"
        assert cache_document["schema_version"] == 2
        jsonschema = pytest.importorskip("jsonschema")
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "get-data-info-cache.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(schema).validate(cache_document)

        cached_handler = handler_class(
            data_path, is_cache=True, head=5, **handler_options
        )

        def fail_recomputation(*args, **kwargs):
            raise AssertionError("A warm cache must not recompute statistics")

        monkeypatch.setattr(cached_handler, "_get_variable_info", fail_recomputation)
        assert cached_handler.info == result
        assert data_path.read_bytes() == source_bytes


@pytest.mark.parametrize("head", [2, -2])
def test_boolean_metrics_and_variable_selection(tmp_path, handler_options, head):
    data_path = tmp_path / "sample.csv"
    data_path.write_text("x,flag\n1,True\n2,False\n", encoding="utf-8")
    handler_options["metrics"] = ["q1", "q3"]
    handler_class = get_data_handler("csv")
    result = handler_class(
        data_path, vars_list=["flag"], head=head, is_cache=False, **handler_options
    ).info

    assert result["overview"]["var_list"] == ["flag"]
    assert list(result["vars_detail"]) == ["flag"]
    assert result["vars_detail"]["flag"]["summary"] == {
        "obs": 2, "mean": 0.5, "stderr": 0.5, "min": 0.0, "max": 1.0,
        "q1": 0.25, "q3": 0.75,
    }
    assert result["head"] == [{"flag": True}, {"flag": False}]

    handler_options["metrics"] = []
    numeric_only = handler_class(
        data_path, vars_list=["x"], is_cache=False, **handler_options
    ).info
    assert list(numeric_only["vars_detail"]) == ["x"]
    bool_default = handler_class(
        data_path, vars_list=["flag"], is_cache=False, **handler_options
    ).info
    assert set(bool_default["vars_detail"]["flag"]["summary"]) == {
        "obs", "mean", "stderr", "min", "max"
    }


@pytest.mark.parametrize("dtype", [None, "boolean"])
def test_missing_boolean_values_are_excluded(tmp_path, handler_options, dtype):
    data_path = tmp_path / "missing.csv"
    data_path.write_text("id,flag\n1,True\n2,\n3,False\n", encoding="utf-8")
    read_options = {} if dtype is None else {"dtype": {"flag": dtype}}
    handler = get_data_handler("csv")(
        data_path, head=3, is_cache=False, **handler_options, **read_options
    )
    original_frame = handler.df.copy(deep=True)

    result = handler.info

    assert result["overview"]["obs"] == 3
    assert result["vars_detail"]["flag"]["type"] == "bool"
    assert result["vars_detail"]["flag"]["summary"]["obs"] == 2
    assert result["vars_detail"]["flag"]["summary"]["mean"] == 0.5
    assert result["vars_detail"]["flag"]["summary"]["stderr"] == 0.5
    assert result["head"][0]["flag"] is True
    assert pd.isna(result["head"][1]["flag"])
    assert result["head"][2]["flag"] is False
    pd.testing.assert_frame_equal(handler.df, original_frame)


def test_version_one_cache_is_preserved_but_not_reused(
    tmp_path, monkeypatch, handler_options
):
    data_path = tmp_path / "legacy.csv"
    data_path.write_text("flag\nTrue\nFalse\n", encoding="utf-8")
    handler_class = get_data_handler("csv")
    with monkeypatch.context() as legacy_settings:
        legacy_settings.setattr(DataInfoBase, "CACHE_SCHEMA_VERSION", 1)
        legacy_handler = handler_class(data_path, **handler_options)
        legacy_handler.summary()
        legacy_path = legacy_handler.cached_file
        legacy_document = json.loads(legacy_path.read_text(encoding="utf-8"))
        legacy_document["vars_detail"]["flag"]["type"] = "float"
        legacy_document["vars_detail"]["flag"]["summary"]["mean"] = 999
        legacy_path.write_text(json.dumps(legacy_document), encoding="utf-8")
        legacy_bytes = legacy_path.read_bytes()

    handler = handler_class(data_path, **handler_options)
    result = handler.info

    assert handler.cached_file != legacy_path
    assert handler.cached_file.exists()
    assert legacy_path.read_bytes() == legacy_bytes
    assert result["vars_detail"]["flag"]["type"] == "bool"
    assert result["vars_detail"]["flag"]["summary"]["mean"] == 0.5


@pytest.mark.parametrize("values", [[], [None, None], [True], [False], [True] * 4])
def test_sparse_boolean_columns_produce_valid_json(tmp_path, handler_options, values):
    data_path = tmp_path / "sparse.csv"
    pd.DataFrame({"flag": pd.Series(values, dtype="boolean")}).to_csv(
        data_path, index=False
    )
    result = get_data_handler("csv")(
        data_path, dtype={"flag": "boolean"}, is_cache=False, **handler_options
    ).info

    detail = result["vars_detail"]["flag"]
    assert detail["type"] == "bool"
    count = sum(value is not None for value in values)
    assert detail["summary"]["obs"] == count
    if count == 0:
        assert all(value is None for key, value in detail["summary"].items() if key != "obs")
    elif count == 1:
        assert detail["summary"]["stderr"] is None
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "series, expected_type",
    [
        (pd.Series([True, False], dtype=bool), "bool"),
        (pd.Series([True, None, False], dtype="boolean"), "bool"),
        (pd.Series([np.bool_(True), None, np.bool_(False)], dtype=object), "bool"),
        (pd.Series(pd.Categorical([True, False])), "bool"),
        (pd.Series([], dtype=bool), "bool"),
        (pd.Series([None, None], dtype="boolean"), "bool"),
        (pd.Series([0, 1]), "float"),
        (pd.Series([0.0, 1.0]), "float"),
        (pd.Series([True, 1], dtype=object), "float"),
        (pd.Series(["True", "False"], dtype="string"), "str"),
    ],
)
def test_boolean_type_detection_does_not_relabel_numeric_data(series, expected_type):
    assert DataInfoBase._determine_variable_type(series) == expected_type
