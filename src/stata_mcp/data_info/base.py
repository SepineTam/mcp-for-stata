#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : data_info/base.py

import copy
import hashlib
import json
import logging
import time
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

from .._diagnostic_logging import (
    elapsed_ms,
    log_event,
    new_request_id,
    source_reference,
    utf8_size,
)

# Global registry for data info classes
# Maps file extensions to their corresponding DataInfoBase subclass
DATA_INFO_REGISTRY: Dict[str, type] = {}
logger = logging.getLogger(__name__)


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
    CACHE_SCHEMA_VERSION = 2
    CACHE_SETTINGS_HASH_LENGTH = 16

    DEFAULT_METRICS: List[str] = [
        'obs', 'mean', 'stderr', 'min', 'max'
    ]
    ALLOWED_METRICS: List[str] = DEFAULT_METRICS + [
        # Additional metrics
        'med', 'q1', 'q3', 'skewness', 'kurtosis'
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
        metrics: List[str] | Tuple[str, ...] | None = None,
        head: int = 0,
        request_id: str | None = None,
        **kwargs
    ):
        self.request_id = request_id or new_request_id()
        self.source_ref = source_reference(data_path)
        self._dataframe_read_count = 0
        self._hash_count = 0
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

        runtime_settings = None
        if any(
            value is None
            for value in (
                string_keep_number,
                decimal_places,
                hash_length,
                metrics,
            )
        ):
            runtime_settings = self._load_default_runtime_settings()

        resolved_string_keep_number = (
            string_keep_number
            if string_keep_number is not None
            else getattr(runtime_settings, "string_keep_number", 10)
        )
        resolved_decimal_places = (
            decimal_places
            if decimal_places is not None
            else getattr(runtime_settings, "decimal_places", 3)
        )
        resolved_hash_length = (
            hash_length
            if hash_length is not None
            else getattr(runtime_settings, "hash_length", 12)
        )
        resolved_metrics = (
            metrics
            if metrics is not None
            else getattr(runtime_settings, "metrics", None)
        )
        self.string_keep_number = (
            int(resolved_string_keep_number)
        )
        self.decimal_places = int(resolved_decimal_places)
        self.HASH_LENGTH = int(resolved_hash_length)
        self._metrics = self._normalize_metrics(resolved_metrics)
        self._head = head
        self._cache_read_options = repr(kwargs)

        self.kwargs = kwargs  # Store additional keyword arguments for subclasses to use

    @classmethod
    def _normalize_metrics(
        cls,
        metrics: List[str] | Tuple[str, ...] | None,
    ) -> List[str]:
        """Return supported metrics in caller order, or the legacy defaults."""
        if metrics is None:
            return list(cls.DEFAULT_METRICS)
        normalized_metrics = [
            str(metric).lower()
            for metric in metrics
            if str(metric).lower() in cls.ALLOWED_METRICS
        ]
        unique_metrics = list(dict.fromkeys(normalized_metrics))
        return unique_metrics or list(cls.DEFAULT_METRICS)

    @staticmethod
    def _load_default_runtime_settings() -> Any | None:
        """Resolve generic settings for callers that instantiate handlers directly."""
        try:
            from ..config import Config

            return Config().get_data_info_config("api")
        except Exception as error:
            logger.warning(
                "Could not resolve default data-info settings: %s",
                error,
            )
            return None

    # Properties
    @cached_property
    def bytes_io_data(self) -> BytesIO:
        started_at = time.perf_counter()
        source_kind = "url" if self.is_url else "local"
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.source_read.started",
            self.request_id,
            source_kind=source_kind,
            source_ref=self.source_ref,
        )
        try:
            data = self._fetch_data() if self.is_url else self._load_data()
        except Exception as error:
            log_event(
                logger,
                logging.ERROR,
                "get_data_info.source_read.failed",
                self.request_id,
                duration_ms=elapsed_ms(started_at),
                error_type=type(error).__name__,
                source_kind=source_kind,
                source_ref=self.source_ref,
            )
            raise
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.source_read.completed",
            self.request_id,
            duration_ms=elapsed_ms(started_at),
            source_bytes=data.getbuffer().nbytes,
            source_kind=source_kind,
            source_ref=self.source_ref,
        )
        return data

    @property
    def hash(self) -> str:
        self._hash_count += 1
        started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.hash.started",
            self.request_id,
            occurrence=self._hash_count,
        )
        digest = hashlib.md5(self.bytes_io_data.getvalue()).hexdigest()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.hash.completed",
            self.request_id,
            duration_ms=elapsed_ms(started_at),
            occurrence=self._hash_count,
        )
        return digest

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
        return self.cache_dir / (
            f"data_info__{self.name}_{self.suffix.strip('.')}__"
            f"hash_{self.hash[: self.HASH_LENGTH]}__"
            f"settings_{self.cache_settings_hash}.json"
        )

    @cached_property
    def cache_settings_hash(self) -> str:
        """Return a stable identity for settings that can change cached output."""
        source_identity = (
            str(self.data_path) if self.is_url else self.data_path.resolve().as_posix()
        )
        cache_settings = {
            "schema_version": self.CACHE_SCHEMA_VERSION,
            "handler": f"{type(self).__module__}.{type(self).__qualname__}",
            "source": source_identity,
            "encoding": self.encoding,
            "read_options": self._cache_read_options,
            "metrics": self.metrics,
            "string_keep_number": self.string_keep_number,
            "decimal_places": self.decimal_places,
            "hash_length": self.HASH_LENGTH,
        }
        serialized_settings = json.dumps(
            cache_settings,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(serialized_settings.encode("utf-8")).hexdigest()[
            : self.CACHE_SETTINGS_HASH_LENGTH
        ]

    @property
    def metrics(self) -> List[str]:
        return list(self._metrics)

    @property
    def df(self) -> pd.DataFrame:
        """Get the data as a pandas DataFrame."""
        self._dataframe_read_count += 1
        read_occurrence = self._dataframe_read_count
        started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.dataframe_read.started",
            self.request_id,
            occurrence=read_occurrence,
            source_ref=self.source_ref,
            suffix=self.suffix.lower(),
        )
        try:
            data_frame = self._read_data()
        except Exception as error:
            log_event(
                logger,
                logging.ERROR,
                "get_data_info.dataframe_read.failed",
                self.request_id,
                duration_ms=elapsed_ms(started_at),
                error_type=type(error).__name__,
                occurrence=read_occurrence,
                source_ref=self.source_ref,
                suffix=self.suffix.lower(),
            )
            raise
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.dataframe_read.completed",
            self.request_id,
            columns=len(data_frame.columns),
            duration_ms=elapsed_ms(started_at),
            occurrence=read_occurrence,
            rows=len(data_frame),
            source_ref=self.source_ref,
            suffix=self.suffix.lower(),
        )
        return data_frame

    @property
    def vars_list(self) -> List[str]:
        """Get the list of selected variables."""
        return self._get_selected_vars(self._pre_vars_list)

    @property
    def info(self) -> Dict[str, Any]:
        """Get comprehensive information about the data."""
        started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.info_pipeline.started",
            self.request_id,
            cache_enabled=self.is_cache,
            head=self._head,
        )
        summary = self.summary()
        stage_started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.variable_filter.started",
            self.request_id,
        )
        result = self._filter(self._filter_var(copy.deepcopy(summary)))
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.variable_filter.completed",
            self.request_id,
            duration_ms=elapsed_ms(stage_started_at),
            selected_variables=len(result.get("vars_detail", {})),
        )
        stage_started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.preview.started",
            self.request_id,
            requested_rows=abs(self._head),
        )
        head_data = self._get_head()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.preview.completed",
            self.request_id,
            duration_ms=elapsed_ms(stage_started_at),
            returned_rows=len(head_data) if head_data is not None else 0,
        )
        if head_data is not None:
            result["head"] = head_data
            requested = abs(self._head)
            actual = len(head_data)
            if actual < requested:
                result["head_warning"] = f"Requested {requested} rows but data has only {actual}"
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.info_pipeline.completed",
            self.request_id,
            dataframe_reads=self._dataframe_read_count,
            duration_ms=elapsed_ms(started_at),
            hash_operations=self._hash_count,
        )
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
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.source_fetch.status",
            self.request_id,
            source_ref=self.source_ref,
            status_code=response.status_code,
        )
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
        started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.summary.started",
            self.request_id,
            cache_enabled=self.is_cache,
        )
        if self.is_cache:
            cached_summary = self.load_cached_summary()
            if cached_summary:
                log_event(
                    logger,
                    logging.DEBUG,
                    "get_data_info.summary.completed",
                    self.request_id,
                    cache_hit=True,
                    duration_ms=elapsed_ms(started_at),
                )
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

        stage_started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.summary.variables.started",
            self.request_id,
            variables=len(all_vars),
        )
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
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.summary.variables.completed",
            self.request_id,
            duration_ms=elapsed_ms(stage_started_at),
            variables=len(all_vars),
        )

        summary_result = {
            "overview": overview,
            "info_config": info_config,
            "vars_detail": vars_detail,
            "saved_path": self.cached_file.as_posix() if self.is_cache else "Result is not saved."
        }

        if self.is_cache:
            self.save_to_json(summary_result)

        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.summary.completed",
            self.request_id,
            cache_hit=False,
            duration_ms=elapsed_ms(started_at),
        )
        return summary_result

    def save_to_json(self, summary: Dict[str, Any]) -> bool:
        saved_path = self.cached_file
        started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.cache_write.started",
            self.request_id,
            cache_ref=source_reference(saved_path),
        )
        try:
            serialized_summary = json.dumps(summary, ensure_ascii=False, indent=4)
            with open(saved_path, "w", encoding="utf-8") as f:
                f.write(serialized_summary)
            log_event(
                logger,
                logging.DEBUG,
                "get_data_info.cache_write.completed",
                self.request_id,
                cache_ref=source_reference(saved_path),
                duration_ms=elapsed_ms(started_at),
                output_utf8_bytes=utf8_size(serialized_summary),
            )
            return True
        except Exception as e:
            log_event(
                logger,
                logging.ERROR,
                "get_data_info.cache_write.failed",
                self.request_id,
                cache_ref=source_reference(saved_path),
                duration_ms=elapsed_ms(started_at),
                error_type=type(e).__name__,
            )
            return False

    def load_cached_summary(self) -> Dict[str, Any] | None:
        """
        Load summary from cache if available and hash matches.

        Returns:
            Dict[str, Any] | None: Full summary from cache or None when unavailable.
        """
        started_at = time.perf_counter()
        cache_path = self.cached_file
        cache_ref = source_reference(cache_path)
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.cache_lookup.started",
            self.request_id,
            cache_ref=cache_ref,
        )
        if not cache_path.exists():
            log_event(
                logger,
                logging.DEBUG,
                "get_data_info.cache_lookup.completed",
                self.request_id,
                cache_ref=cache_ref,
                duration_ms=elapsed_ms(started_at),
                outcome="miss_not_found",
            )
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_summary = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log_event(
                logger,
                logging.ERROR,
                "get_data_info.cache_lookup.failed",
                self.request_id,
                cache_ref=cache_ref,
                duration_ms=elapsed_ms(started_at),
                error_type=type(e).__name__,
            )
            return None

        cached_hash = cached_summary.get("overview", {}).get("hash")
        if cached_hash != self.hash:
            log_event(
                logger,
                logging.DEBUG,
                "get_data_info.cache_lookup.completed",
                self.request_id,
                cache_ref=cache_ref,
                duration_ms=elapsed_ms(started_at),
                outcome="miss_hash_mismatch",
            )
            return None

        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.cache_lookup.completed",
            self.request_id,
            cache_ref=cache_ref,
            duration_ms=elapsed_ms(started_at),
            outcome="hit",
        )
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
            numeric_series = pd.to_numeric(non_na_series, errors='raise')
            return NumericSeries(data=numeric_series, max_decimal_places=self.decimal_places)

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
