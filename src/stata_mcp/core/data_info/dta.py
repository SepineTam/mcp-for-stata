#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : dta.py

from io import BytesIO
from typing import Any, Dict

import pandas as pd

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
            ValueError: If the file is not a valid Stata file
        """
        # Get data as BytesIO (handles both URL and local file)
        # Note: StataReader consumes the buffer, so we need to work with copies
        buffer = self.bytes_io_data

        try:
            # StataReader needs its own buffer copy as it modifies the stream
            # Create a copy for reading labels
            label_buffer = BytesIO(buffer.getvalue())

            # Read variable labels using StataReader
            with pd.io.stata.StataReader(label_buffer) as reader:
                self._variable_labels = reader.variable_labels()

            # Create another copy for reading the DataFrame
            data_buffer = BytesIO(buffer.getvalue())

            df = pd.read_stata(
                data_buffer,
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
