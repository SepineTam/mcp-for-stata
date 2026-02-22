#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : xlsx.py

from pathlib import Path

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
            FileNotFoundError: If the local file does not exist
            ValueError: If the file is not a valid Excel file
        """
        if self.is_url:
            source = str(self.data_path)
        else:
            file_path = Path(self.data_path)

            if not file_path.exists():
                raise FileNotFoundError(f"Excel file not found: {file_path}")

            if self.suffix.lower() not in self.supported_extensions:
                raise ValueError(f"File must have extension in {self.supported_extensions}, got: {self.suffix}")

            source = file_path

        try:
            df = pd.read_excel(source, **self.kwargs)
            return df
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                filtered_kwargs = {k: v for k, v in self.kwargs.items() if k in {"sheet_name", "header", "names"}}
                df = pd.read_excel(source, **filtered_kwargs)
                return df
            raise ValueError(f"Error reading Excel file {source}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error reading Excel file {source}: {str(e)}")
