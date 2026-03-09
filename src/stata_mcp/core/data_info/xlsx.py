#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : xlsx.py

from io import BytesIO

import pandas as pd

from .base import DataInfoBase


class ExcelDataInfo(DataInfoBase):
    """Data info handler for Excel files."""

    supported_extensions = ['xlsx', 'xls']

    def _read_data(self) -> pd.DataFrame:
        """
        Read Excel file into pandas DataFrame.

        Supports .xlsx and .xls files from local paths or URLs.

        Returns:
            pd.DataFrame: The data from the Excel file

        Raises:
            ValueError: If the file is not a valid Excel file
        """
        # Get data as BytesIO (handles both URL and local file)
        buffer = self.bytes_io_data

        try:
            # Create a copy for pandas to read
            data_buffer = BytesIO(buffer.getvalue())
            df = pd.read_excel(data_buffer, **self.kwargs)
            return df

        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                filtered_kwargs = {k: v for k, v in self.kwargs.items()
                                   if k in {"sheet_name", "header", "names"}}
                data_buffer = BytesIO(buffer.getvalue())
                df = pd.read_excel(
                    data_buffer, **filtered_kwargs
                )
                return df
            raise ValueError(f"Error reading Excel file {self.data_path}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error reading Excel file {self.data_path}: {str(e)}")
