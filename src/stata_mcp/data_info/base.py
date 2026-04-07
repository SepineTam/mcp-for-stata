#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : _base.py

import copy
import hashlib
import json
import logging
import os
import tomllib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests

# Global registry for data info classes
# Maps file extensions to their corresponding DataInfoBase subclass
DATA_INFO_REGISTRY: Dict[str, type] = {}


@dataclass
class Series:
    data: pd.Series

    def get_summary(self) -> Dict[str, Any]:
        ...


@dataclass
class StringSeries(Series):
    max_display: int = 10

    def get_summary(self) -> Dict[str, Any]:
        return {
            "obs": self.obs,
            "value_list": self.value_list
        }

    @property
    def obs(self) -> int:
        return int(self.data.size)

    @property
    def value_list(self) -> List[str]:
        unique_values = self.data.unique()

        value_list = (
            sorted(unique_values.tolist())
            if len(unique_values) <= self.max_display
            else sorted(np.random.choice(unique_values, self.max_display, replace=False).tolist())
        )
        return value_list


@dataclass
class NumericSeries(Series):
    max_decimal_places: int = 3

    def get_summary(self) -> Dict[str, Any]:
        return {
            "obs": self.obs,
            "mean": self.mean,
            "stderr": self.stderr,
            "min": self.min,
            "max": self.max,
            "q1": self.q1,
            "med": self.med,
            "q3": self.q3,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
        }

    @property
    def obs(self) -> int:
        return int(self.data.size)

    @property
    def min(self) -> float:
        return round(float(self.data.min()), self.max_decimal_places)

    @property
    def max(self) -> float:
        return round(float(self.data.max()), self.max_decimal_places)

    @property
    def med(self) -> float:
        return round(float(self.data.median()), self.max_decimal_places)

    @property
    def q1(self) -> float:
        return round(float(self.data.quantile(0.25)), self.max_decimal_places)

    @property
    def q3(self) -> float:
        return round(float(self.data.quantile(0.75)), self.max_decimal_places)

    @property
    def mean(self) -> float:
        return round(float(self.data.mean()), self.max_decimal_places)

    @property
    def stderr(self) -> float:
        return round(float(np.std(self.data, ddof=1) / np.sqrt(self.obs)), self.max_decimal_places)

    @property
    def skewness(self) -> float:
        return round(float(self.data.skew()), self.max_decimal_places)

    @property
    def kurtosis(self) -> float:
        return round(float(self.data.kurtosis()), self.max_decimal_places)


class DataInfoBase(ABC):
    """Base class for data info handlers."""

    # Registry of supported file extensions (to be overridden by subclasses)
    supported_extensions: List[str] = []

    CFG_FILE = Path.home() / ".statamcp" / "config.toml"
    DEFAULT_METRICS: List[str] = [
        'obs', 'mean', 'stderr', 'min', 'max'
    ]
    ALLOWED_METRICS: List[str] = DEFAULT_METRICS + [
        # Additional metrics
        'q1', 'q3', 'skewness', 'kurtosis'
    ]

    # Request timeout
    DEFAULT_TIMEOUT = (5, 30)

    def __init_subclass__(cls, **kwargs):
        """
        Automatically register subclasses to DATA_INFO_REGISTRY.

        This method is called when a subclass is created, and it registers
        the subclass with its supported file extensions in the global registry.
        """
        super().__init_subclass__(**kwargs)

        # Register this subclass for each supported extension
        for ext in cls.supported_extensions:
            DATA_INFO_REGISTRY[ext.lower()] = cls

    def __init__(
        self,
        data_path: str | PathLike | Path,
        vars_list: List[str] | str = None,
        *,
        encoding: str = "utf-8",
        is_cache: bool = True,
        cache_dir: str | Path = None,
        string_keep_number: int = None,
        decimal_places: int = None,
        hash_length: int = None,
        head: int = 5,
        **kwargs
    ):
        if isinstance(data_path, str):
            self.is_url = self._is_url(data_path)
            if not self.is_url:  # if it is a local file, convert it to a Path object
                data_path = Path(data_path)
            self.data_path = data_path
        elif isinstance(data_path, (Path, PathLike)):
            self.is_url = False
            data_path = Path(data_path)
        else:
            raise TypeError("data_path must be a string or PathLike object.")

        self.data_path = data_path
        if not self.is_url:
            if not self.data_path.exists():
                raise FileNotFoundError(f"Data file not found: {self.data_path}")

        self.encoding = encoding
        self._pre_vars_list = vars_list

        self.is_cache = is_cache
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".statamcp" / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.string_keep_number = string_keep_number or int(os.getenv("STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER", 10))
        self.decimal_places = decimal_places or int(os.getenv("STATA_MCP_DATA_INFO_DECIMAL_PLACES", 3))
        self.HASH_LENGTH = hash_length or int(os.getenv("STATA_MCP_DATA_INFO_HASH_LENGTH", "12"))
        self._head = head

        self.kwargs = kwargs  # Store additional keyword arguments for subclasses to use

    # Properties
    @cached_property
    def bytes_io_data(self) -> BytesIO:
        if self.is_url:
            return self._fetch_data()
        else:
            return self._load_data()

    @property
    def hash(self) -> str:
        return hashlib.md5(self.bytes_io_data.getvalue()).hexdigest()

    @property
    def name(self) -> str:
        if self.is_url:
            return self.data_path.split("/")[-1].split('.')[0]
        else:
            return self.data_path.stem

    @property
    def suffix(self) -> str:
        if self.is_url:
            return self.data_path.split("/")[-1].split('.')[-1]
        else:
            return self.data_path.suffix.strip(".")

    @property
    def cached_file(self) -> Path:
        return self.cache_dir / f"data_info__{self.name}_{self.suffix.strip('.')}__hash_{self.hash[:self.HASH_LENGTH]}.json"

    @property
    def metrics(self) -> List[str]:
        try:
            with open(self.CFG_FILE, "rb") as f:
                config = tomllib.load(f)

            additional = config.get("data_info", {}).get("metrics", []) or []
            if not isinstance(additional, list):
                additional = [additional]

            target = (set(self.DEFAULT_METRICS) | set(additional)) & set(self.ALLOWED_METRICS)

            return list(dict.fromkeys(
                [m for m in self.DEFAULT_METRICS if m in target] +
                [m for m in self.ALLOWED_METRICS if m in target]
            ))
        except (FileNotFoundError, OSError, Exception):
            return self.DEFAULT_METRICS

    @property
    def df(self) -> pd.DataFrame:
        """Get the data as a pandas DataFrame."""
        return self._read_data()

    @property
    def vars_list(self) -> List[str]:
        """Get the list of selected variables."""
        return self._get_selected_vars(self._pre_vars_list)

    @property
    def info(self) -> Dict[str, Any]:
        """Get comprehensive information about the data."""
        summary = self.summary()
        result = self._filter(self._filter_var(copy.deepcopy(summary)))
        head_data = self._get_head()
        if head_data is not None:
            result["head"] = head_data
            requested = abs(self._head)
            actual = len(head_data)
            if actual < requested:
                result["head_warning"] = f"Requested {requested} rows but data has only {actual}"
        return result

    @property
    def data_source(self) -> str:
        if self.is_url:
            return str(self.data_path)
        else:
            return self.data_path.as_posix()

    # Abstract methods (must be implemented by subclasses)
    @abstractmethod
    def _read_data(self) -> pd.DataFrame:
        """Read data from the source file. Must be implemented by subclasses."""
        ...

    def _fetch_data(
        self,
        timeout: Tuple[int, int] = None
    ) -> BytesIO:
        """
        Fetch data from URL into memory.

        Args:
            timeout: (connect_timeout, read_timeout) in seconds.
                     Defaults to (5, 30) if not specified.

        Returns:
            BytesIO: In-memory byte buffer containing the downloaded data.

        Raises:
            requests.RequestException: If the request fails or times out.
        """
        request_timeout = timeout or self.DEFAULT_TIMEOUT

        response = requests.get(
            str(self.data_path),
            timeout=request_timeout
        )
        response.raise_for_status()
        return BytesIO(response.content)

    def _load_data(self) -> BytesIO:
        """
        Load data from local file into memory.

        Returns:
            BytesIO: In-memory byte buffer containing the file data.
        """
        return BytesIO(self.data_path.read_bytes())

    # Public methods
    def summary(self) -> Dict[str, Any]:
        """
        Provide a summary of the data.

        Returns:
            Dict[str, Any]: the summary of provided data (vars)

        Examples:
            >>> from stata_mcp.data_info import DtaDataInfo
            >>> data_info = DtaDataInfo("/Applications/Stata/auto.dta")
            >>> summary_data = data_info.summary()
            >>> print(summary_data)
            {
                "overview": {
                    "source": "/Applications/Stata/auto.dta",
                    "obs": 74,
                    "var_numbers": 12,
                    "var_list": ["make", "price", "mpg", "rep78", "headroom", "trunk",
                                 "weight", "length", "turn", "displacement", "gear_ratio", "foreign"],
                    "hash": "c557a2db346b522404c2f22932048de4"
                },
                "info_config": {
                    "metrics": ["obs", "mean", "stderr", "min", "max"],
                    "max_display": 10,
                    "decimal_places": 3
                },
                "vars_detail": {
                    "make": {
                        "type": "str",
                        "var": "make",
                        "summary": {
                            "obs": 74,
                            "value_list": ["AMC Pacer", "Chev. Chevette", "Chev. Nova",
                                          "Honda Accord", "Merc. Monarch", "Olds Cutl Supr",
                                          "Olds Delta 88", "Pont. Catalina", "Renault Le Car", "Volvo 260"]
                        }
                    },
                    "price": {
                        "type": "float",
                        "var": "price",
                        "summary": {
                            "obs": 74,
                            "mean": 6165.257,
                            "stderr": 342.872,
                            "min": 3291.0,
                            "max": 15906.0,
                            "q1": 4220.25,
                            "med": 5006.5,
                            "q3": 6332.25,
                            "skewness": 1.688,
                            "kurtosis": 2.034
                        }
                    },
                    "mpg": {
                        "type": "float",
                        "var": "mpg",
                        "summary": {
                            "obs": 74,
                            "mean": 21.297,
                            "stderr": 0.673,
                            "min": 12.0,
                            "max": 41.0,
                            "q1": 18.0,
                            "med": 20.0,
                            "q3": 24.75,
                            "skewness": 0.968,
                            "kurtosis": 1.13
                        }
                    },
                    "rep78": {
                        "type": "float",
                        "var": "rep78",
                        "summary": {
                            "obs": 69,
                            "mean": 3.406,
                            "stderr": 0.119,
                            "min": 1.0,
                            "max": 5.0,
                            "q1": 3.0,
                            "med": 3.0,
                            "q3": 4.0,
                            "skewness": -0.058,
                            "kurtosis": -0.254
                        }
                    }
                },
                "saved_path": "~/.statamcp/.cache/data_info__auto_dta__hash_c557a2db346b.json"
            }
        """
        if self.is_cache:
            cached_summary = self.load_cached_summary()
            if cached_summary:
                return cached_summary
        df = self.df
        all_vars = list(df.columns)

        # Basic information (full overview with all vars)
        overview = {
            "source": self.data_source,
            "obs": len(df),
            "var_numbers": len(all_vars),
            "var_list": all_vars,
            "hash": self.hash,
        }
        info_config = {
            "metrics": self.metrics,
            "max_display": self.string_keep_number,
            "decimal_places": self.decimal_places
        }
        vars_detail = {}

        for var_name in all_vars:
            var_series = df[var_name]
            series_obj = self._get_variable_info(var_series)

            # Determine variable type for the info dict
            var_type = "str" if isinstance(series_obj, StringSeries) else "float"

            # Build variable info dictionary
            var_info = {
                "type": var_type,
                "var": var_name,
                "summary": series_obj.get_summary()
            }
            # Merge extra info from subclass
            var_info.update(self._get_var_extra_info(var_name))

            vars_detail[var_name] = var_info

        summary_result = {
            "overview": overview,
            "info_config": info_config,
            "vars_detail": vars_detail,
            "saved_path": self.cached_file.as_posix() if self.is_cache else "Result is not saved."
        }

        if self.is_cache:
            self.save_to_json(summary_result)

        return summary_result

    def save_to_json(self, summary: Dict[str, Any]) -> bool:
        saved_path = self.cached_file
        try:
            with open(saved_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(summary, ensure_ascii=False, indent=4))
            return True
        except Exception as e:
            logging.error(f"Error saving summary to JSON: {str(e)}")
            return False

    def load_cached_summary(self) -> Dict[str, Any] | None:
        """
        Load summary from cache if available and hash matches.

        Returns:
            Dict[str, Any] | None: Full summary from cache or None when unavailable.
        """
        if not self.cached_file.exists():
            return None

        try:
            with open(self.cached_file, "r", encoding="utf-8") as f:
                cached_summary = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logging.error(f"Error loading cached summary: {str(e)}")
            return None

        cached_hash = cached_summary.get("overview", {}).get("hash")
        if cached_hash != self.hash:
            return None

        return cached_summary

    # Private helper methods
    def _filter(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter the summary result to the animation format.

        Key Points:
            1. keep self.metrics for numerical vars;
            2. keep self.string_keep_number values for string vars.

        Args:
            summary (Dict): the summary result <- self.summary()

        Returns:
            Dict: filtered summary
        """
        var_list = summary.get("vars_detail", {}).keys()
        for var_name in var_list:
            var_detail = summary.get("vars_detail", {}).get(var_name)
            if var_detail.get("type") == "float":
                # Filter numerical vars based on self.metrics
                var_summary = var_detail["summary"]
                filtered_summary = {k: var_summary[k] for k in self.metrics if k in var_summary}
                summary["vars_detail"][var_name]["summary"] = filtered_summary

        return summary

    def _filter_var(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Filter cached summary to keep only variables in self.vars_list."""
        target_vars = self.vars_list or []
        cached_vars = summary.get("vars_detail", {})
        filtered_vars_detail = {var: cached_vars[var] for var in target_vars if var in cached_vars}

        summary["vars_detail"] = filtered_vars_detail
        if "overview" in summary:
            summary["overview"]["var_list"] = list(target_vars)
            summary["overview"]["var_numbers"] = len(summary["overview"]["var_list"])

        return summary

    def _get_selected_vars(self, vars: List[str] | str = None) -> List[str]:
        """
        Get the list of selected variables.

        If vars is None, return all variables from self.data.
        If vars is a string, convert it to a list.
        Check if all variables exist in self.data, if not raise an error and return all available variables.

        Args:
            vars: List of variable names, single variable name, or None.

        Returns:
            List[str]: List of selected variable names.

        Raises:
            ValueError: If specified variables don't exist in the dataset.
        """
        # Get all available variables from the data
        all_vars = list(self.df.columns)

        if vars is None:
            return all_vars

        # Convert string to list if needed
        if isinstance(vars, str):
            vars = [vars]

        # Check if all specified variables exist in the dataset
        missing_vars = [var for var in vars if var not in all_vars]

        if missing_vars:
            raise ValueError(f"Variables {missing_vars} not found in dataset. "
                             f"Available variables are: {all_vars}")

        return vars

    # Helper methods for summary
    def _get_variable_info(self, var_series: pd.Series) -> Series:
        """
        Create a Series object (StringSeries or NumericSeries) for a variable.

        Args:
            var_series: pandas Series containing the variable data

        Returns:
            Series: StringSeries or NumericSeries object
        """
        # Remove NA values for analysis
        non_na_series = var_series.dropna()

        # Determine variable type
        var_type = DataInfoBase._determine_variable_type(non_na_series)

        # Create appropriate Series object
        if var_type == "str":
            return StringSeries(data=non_na_series, max_display=self.string_keep_number)
        else:  # float type
            return NumericSeries(data=non_na_series, max_decimal_places=self.decimal_places)

    def _get_head(self) -> List[Dict[str, Any]] | None:
        """Get preview rows from the DataFrame, filtered by vars_list."""
        if self._head == 0:
            return None
        df = self.df[self.vars_list]
        if self._head > 0:
            return df.head(self._head).to_dict(orient="records")
        return df.tail(abs(self._head)).to_dict(orient="records")

    def _get_var_extra_info(self, var_name: str) -> Dict[str, Any]:
        """
        Get extra information for a variable. Override in subclasses.

        Args:
            var_name: Variable name

        Returns:
            Dict with extra fields to add to var_info
        """
        return {}

    @staticmethod
    def _determine_variable_type(series: pd.Series) -> str:
        """
        Determine the type of variable.

        Args:
            series: pandas Series with NA values removed

        Returns:
            str: "str" for string variables, "float" for numeric variables
        """
        if len(series) == 0:
            return "float"  # Default to float for empty series

        # Check if all non-null values are numeric
        try:
            # Try to convert to numeric
            pd.to_numeric(series, errors='raise')
            return "float"
        except (ValueError, TypeError):
            return "str"

    @staticmethod
    def _is_url(data_path) -> bool:
        try:
            result = urlparse(str(data_path))
            return all([result.scheme, result.netloc])
        except Exception:
            return False
