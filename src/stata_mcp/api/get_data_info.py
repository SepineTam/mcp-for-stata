#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : get_data_info.py

import json
from pathlib import Path
from typing import List

from ..data_info import get_data_handler
from ._runtime import create_runtime_context


def get_data_info(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    config_file: str | Path | None = None,
) -> str:
    """Return descriptive statistics for a supported dataset."""
    runtime = create_runtime_context(config_file=config_file)
    resolved_data_path = Path(data_path).expanduser().resolve()
    data_extension = resolved_data_path.suffix.lower().strip(".")

    data_info_cls = get_data_handler(data_extension)
    if not data_info_cls:
        return f"Unsupported file extension now: {data_extension}"

    data_info = data_info_cls(
        resolved_data_path,
        vars_list,
        encoding=encoding,
        cache_dir=runtime.tmp_base_path,
    )
    try:
        return json.dumps(data_info.info, ensure_ascii=False)
    except Exception as error:
        return f"Failed to generate data summary for {resolved_data_path}: {error}"
