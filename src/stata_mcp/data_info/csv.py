#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : csv.py

from io import BytesIO

import pandas as pd

from .base import DataInfoBase


class CsvDataInfo(DataInfoBase):
    """Data info handler for CSV and related delimited files."""

    supported_extensions = ['csv', 'tsv', 'psv']

    def _read_data(self) -> pd.DataFrame:
        """
        Read CSV file into pandas DataFrame.

        Supports local files and URLs. Automatically detects header.

        Returns:
            pd.DataFrame: The data from the CSV file

        Raises:
            ValueError: If the file is not a valid CSV file
        """
        self._before_read()

        # Get data as BytesIO (handles both URL and local file)
        buffer = self.bytes_io_data

        # Check file extension
        if self.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"File must have extension in {self.supported_extensions}, got: {self.suffix}")

        try:
            # Auto-detect header if not explicitly specified
            if 'header' not in self.kwargs:
                sample_kwargs = {k: v for k, v in self.kwargs.items() if k not in ['header', 'names']}

                # Create a copy for header detection
                sample_buffer = BytesIO(buffer.getvalue())

                try:
                    df_with_header = pd.read_csv(sample_buffer, nrows=10, header=0, **sample_kwargs)
                    column_names = df_with_header.columns.tolist()

                    # Check if column names look like data values
                    looks_like_data = False
                    for col_name in column_names:
                        try:
                            float(str(col_name))
                            looks_like_data = True
                            break
                        except (ValueError, TypeError):
                            continue

                    if looks_like_data:
                        self.kwargs['header'] = None
                    else:
                        self.kwargs['header'] = 0

                except Exception:
                    self.kwargs['header'] = 0

            # Handle no-header case by providing default column names
            if self.kwargs.get('header') is None:
                sample_kwargs = {k: v for k, v in self.kwargs.items() if k not in ['header', 'names']}
                sample_buffer = BytesIO(buffer.getvalue())
                sample_df = pd.read_csv(sample_buffer, nrows=1, header=None, **sample_kwargs)
                num_cols = len(sample_df.columns)
                self.kwargs['names'] = [f'V{i+1}' for i in range(num_cols)]

            # Read the full CSV file
            data_buffer = BytesIO(buffer.getvalue())

            try:
                df = pd.read_csv(
                    data_buffer, encoding=self.encoding, **self.kwargs
                )
            except TypeError as e:
                if "unexpected keyword argument" in str(e):
                    basic_kwargs = {k: v for k, v in self.kwargs.items()
                                    if k in {'sep', 'header', 'encoding', 'names'}}
                    data_buffer = BytesIO(buffer.getvalue())
                    df = pd.read_csv(data_buffer, **basic_kwargs)
                else:
                    raise

            return df

        except Exception as e:
            raise ValueError(f"Error reading CSV file {self.data_path}: {str(e)}")

    def _before_read(self):
        """Set separator based on file extension."""
        if "sep" in self.kwargs and self.kwargs.get("sep") is None:
            if self.suffix.lower() == "tsv":
                self.kwargs["sep"] = "\t"
            elif self.suffix.lower() == "psv":
                self.kwargs["sep"] = "|"
