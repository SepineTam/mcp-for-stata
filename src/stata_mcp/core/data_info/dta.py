#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : dta.py

from io import BytesIO
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import requests

from .base import DataInfoBase


class DtaDataInfo(DataInfoBase):
    """Data info handler for Stata .dta files."""

    supported_extensions = ['dta']
    _variable_labels: Dict[str, str] = {}

    def _read_data(self) -> pd.DataFrame:
        """
        Read Stata dta file into pandas DataFrame.

        Returns:
            pd.DataFrame: The data from the Stata file

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is not a valid Stata file
        """
        # Check if it's a URL first
        if self.is_url:
            # For URLs, validate the file extension from the URL string
            from urllib.parse import urlparse
            parsed_url = urlparse(str(self.data_path))
            url_path = parsed_url.path
            if not url_path.lower().endswith('.dta'):
                raise ValueError(f"URL must point to a .dta file, got: {url_path}")
            file_path = None  # Not used for URLs
        else:
            # For local files, convert to Path object and validate
            file_path = Path(self.data_path)

            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"Stata file not found: {file_path}")

            # Check if it's a .dta file
            if file_path.suffix.lower() != '.dta':
                raise ValueError(f"File must have .dta extension, got: {file_path.suffix}")

        try:
            # Read the Stata file
            # Using read_stata with convert_categoricals=False to avoid converting labels to categories
            # This preserves the original data structure without converting value labels
            buffer = None
            if self.is_url:
                resp = requests.get(self.data_path)
                resp.raise_for_status()
                buffer = BytesIO(resp.content)

            # Read variable labels using StataReader
            with pd.io.stata.StataReader(buffer if buffer else file_path) as reader:
                self._variable_labels = reader.variable_labels()

            # Reset buffer position after reading labels
            if buffer:
                buffer.seek(0)

            df = pd.read_stata(
                buffer if buffer else file_path,
                convert_categoricals=False,  # disable change data to mapped str.
                convert_dates=True,
                convert_missing=False,
                preserve_dtypes=True
            )
            return df

        except Exception as e:
            raise ValueError(f"Error reading Stata file {self.data_path}: {str(e)}")

    def _get_var_extra_info(self, var_name: str) -> Dict[str, Any]:
        """
        Return variable label for dta files.

        Args:
            var_name: Variable name

        Returns:
            Dict with label field if the variable has a label
        """
        label = self._variable_labels.get(var_name, "")
        return {"label": label} if label else {}
