#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞), Claude Code, GLM-5
# @Email  : sepinetam@gmail.com
# @File   : spss.py

# Notes: This feat is worked by Claude Code with GLM-5

import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pyreadstat
import requests

from .._diagnostic_logging import elapsed_ms, log_event
from .base import DataInfoBase

logger = logging.getLogger(__name__)


class SpssDataInfo(DataInfoBase):
    """Data info handler for SPSS .sav and .zsav files."""

    supported_extensions = ['sav', 'zsav']
    _variable_labels: Dict[str, str] = {}

    def _read_data(self) -> pd.DataFrame:
        """
        Read SPSS data file into pandas DataFrame.

        Returns:
            pd.DataFrame: The data from the SPSS file

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is not a valid SPSS file
        """
        url_path = ""
        if self.is_url:
            from urllib.parse import urlparse
            parsed_url = urlparse(str(self.data_path))
            url_path = parsed_url.path
            valid_extensions = ('.sav', '.zsav')
            if not url_path.lower().endswith(valid_extensions):
                raise ValueError(f"URL must point to an SPSS file, got: {url_path}")

        try:
            if self.is_url:
                stage_started_at = time.perf_counter()
                log_event(
                    logger,
                    logging.DEBUG,
                    "get_data_info.spss_download.started",
                    self.request_id,
                    source_ref=self.source_ref,
                )
                resp = requests.get(str(self.data_path), timeout=self.DEFAULT_TIMEOUT)
                resp.raise_for_status()
                log_event(
                    logger,
                    logging.DEBUG,
                    "get_data_info.spss_download.completed",
                    self.request_id,
                    duration_ms=elapsed_ms(stage_started_at),
                    source_bytes=len(resp.content),
                    source_ref=self.source_ref,
                    status_code=resp.status_code,
                )
                suffix = Path(url_path).suffix
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(resp.content)
                    tmp_path = tmp.name
                try:
                    stage_started_at = time.perf_counter()
                    log_event(
                        logger,
                        logging.DEBUG,
                        "get_data_info.spss_parse.started",
                        self.request_id,
                        source_kind="downloaded_temp_file",
                        source_ref=self.source_ref,
                    )
                    df, meta = pyreadstat.read_sav(tmp_path)
                    log_event(
                        logger,
                        logging.DEBUG,
                        "get_data_info.spss_parse.completed",
                        self.request_id,
                        columns=len(df.columns),
                        duration_ms=elapsed_ms(stage_started_at),
                        rows=len(df),
                        source_kind="downloaded_temp_file",
                        source_ref=self.source_ref,
                    )
                finally:
                    Path(tmp_path).unlink(missing_ok=True)
            else:
                file_path = Path(self.data_path)
                if not file_path.exists():
                    raise FileNotFoundError(f"SPSS file not found: {file_path}")
                stage_started_at = time.perf_counter()
                log_event(
                    logger,
                    logging.DEBUG,
                    "get_data_info.spss_parse.started",
                    self.request_id,
                    source_bytes=file_path.stat().st_size,
                    source_kind="local",
                    source_ref=self.source_ref,
                )
                df, meta = pyreadstat.read_sav(file_path)
                log_event(
                    logger,
                    logging.DEBUG,
                    "get_data_info.spss_parse.completed",
                    self.request_id,
                    columns=len(df.columns),
                    duration_ms=elapsed_ms(stage_started_at),
                    rows=len(df),
                    source_kind="local",
                    source_ref=self.source_ref,
                )

            # column_labels is a list, convert to dict mapping column name -> label
            if meta.column_labels:
                self._variable_labels = dict(zip(df.columns, meta.column_labels))
            else:
                self._variable_labels = {}
            return df

        except Exception as e:
            raise ValueError(f"Error reading SPSS file {self.data_path}: {str(e)}")

    def _get_var_extra_info(self, var_name: str) -> Dict[str, Any]:
        """
        Return variable label for SPSS files.

        Args:
            var_name: Variable name

        Returns:
            Dict with label field if the variable has a label
        """
        label = self._variable_labels.get(var_name, "")
        return {"label": label} if label else {}
