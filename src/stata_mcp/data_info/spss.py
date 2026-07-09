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
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import pyreadstat
import requests

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
                resp = requests.get(str(self.data_path), timeout=self.DEFAULT_TIMEOUT)
                resp.raise_for_status()
                safe_url = parsed_url._replace(query="", fragment="").geturl()
                logger.info("Fetched SPSS data from URL: %s, status=%s", safe_url, resp.status_code)
                suffix = Path(url_path).suffix
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(resp.content)
                    tmp_path = tmp.name
                try:
                    df, meta = pyreadstat.read_sav(tmp_path)
                finally:
                    Path(tmp_path).unlink(missing_ok=True)
            else:
                file_path = Path(self.data_path)
                if not file_path.exists():
                    raise FileNotFoundError(f"SPSS file not found: {file_path}")
                df, meta = pyreadstat.read_sav(file_path)

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
