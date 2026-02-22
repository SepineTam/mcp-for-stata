#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : csv.py

from pathlib import Path

import pandas as pd

from .base import DataInfoBase


class CsvDataInfo(DataInfoBase):
    """Data info handler for CSV and related delimited files."""

    supported_extensions = ['csv', 'tsv', 'psv']

    def _read_data(self) -> pd.DataFrame:
        """
        Read CSV file into pandas DataFrame.

        Automatically detects header and handles various CSV formats.

        Returns:
            pd.DataFrame: The data from the CSV file

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file is not a valid CSV file
        """
        self._before_read()

        # Convert to Path object if it's a string
        file_path = Path(self.data_path)

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Check if it's a CSV file
        if self.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"File must have extension in {self.supported_extensions}, got: {self.suffix}")

        try:
            # Auto-detect header if not explicitly specified
            if 'header' not in self.kwargs:
                # Read first few lines to detect header
                sample_kwargs = {k: v for k, v in self.kwargs.items() if k not in ['header', 'names']}

                # Try reading with header=0 (assume first row is header)
                try:
                    df_with_header = pd.read_csv(file_path, nrows=10, header=0, **sample_kwargs)

                    # Simple heuristic: check if column names look like data values
                    # If column names are all numeric or look like data, probably no header
                    column_names = df_with_header.columns.tolist()

                    # Check if any column name looks like a data value (numeric)
                    looks_like_data = False
                    for col_name in column_names:
                        # Try to convert column name to float
                        try:
                            float(str(col_name))
                            looks_like_data = True
                            break
                        except (ValueError, TypeError):
                            continue

                    if looks_like_data:
                        # Column names look like data values, so no header
                        self.kwargs['header'] = None
                    else:
                        # Column names don't look like data, assume header exists
                        self.kwargs['header'] = 0

                except Exception:
                    # If detection fails, default to header=0
                    self.kwargs['header'] = 0

            # Handle no-header case by providing default column names
            if self.kwargs.get('header') is None:
                # First, read a sample to determine number of columns
                sample_kwargs = {k: v for k, v in self.kwargs.items() if k not in ['header', 'names']}
                sample_df = pd.read_csv(file_path, nrows=1, header=None, **sample_kwargs)
                num_cols = len(sample_df.columns)

                # Generate default column names
                self.kwargs['names'] = [f'V{i+1}' for i in range(num_cols)]

            # Read the CSV file with error handling for invalid parameters
            try:
                df = pd.read_csv(file_path, **self.kwargs)
            except TypeError as e:
                if "unexpected keyword argument" in str(e):
                    # Filter out problematic parameters and retry with basic ones
                    basic_kwargs = {k: v for k, v in self.kwargs.items()
                                    if k in {'sep', 'header', 'encoding', 'names'}}
                    print(f"Warning: Retrying CSV read with filtered parameters due to: {e}")
                    df = pd.read_csv(file_path, **basic_kwargs)
                else:
                    raise
            except Exception as e:
                raise ValueError(f"Error reading CSV file {file_path}: {str(e)}")

            return df

        except Exception as e:
            raise ValueError(f"Error reading CSV file {file_path}: {str(e)}")

    def _before_read(self):
        if "sep" in self.kwargs and self.kwargs.get("sep") is None:
            if self.suffix.lower() == ".tsv":
                self.kwargs["sep"] = "\t"
            elif self.suffix.lower() == ".psv":
                self.kwargs["sep"] = "|"
