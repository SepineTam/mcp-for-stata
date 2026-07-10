#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : api/get_data_info.py

import json
import logging
from pathlib import Path
from typing import List

from ..data_info import get_data_handler
from ..guard.data_path_auditor import DataPathAuditor
from ._runtime import create_runtime_context


def _get_data_info_impl(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    config_file: str | Path | None = None,
    *,
    head: int = 0,
) -> str:
    """Return descriptive statistics for a supported dataset."""
    runtime = create_runtime_context(config_file=config_file)
    auditor = DataPathAuditor(
        working_dir=runtime.config.WORKING_DIR,
        strict_local_boundary=runtime.config.STRICT_DATA_INFO_LOCAL_BOUNDARY,
        enable_url_guard=runtime.config.ENABLE_DATA_INFO_URL_GUARD,
        allowed_url_domains=runtime.config.DATA_INFO_ALLOWED_URL_DOMAINS,
    )

    if auditor.is_url(data_path):
        validated_data = auditor.validate_url(data_path)
        if not isinstance(validated_data, tuple):
            return validated_data
        resolved_data_path, data_extension = validated_data
    else:
        validated_data_path = auditor.validate_local_path(data_path)
        if isinstance(validated_data_path, str):
            return validated_data_path
        resolved_data_path = validated_data_path
        data_extension = resolved_data_path.suffix.lower().strip(".")

    data_info_cls = get_data_handler(data_extension)
    if not data_info_cls:
        logging.warning("Unsupported file extension for data_info: %s", data_extension)
        return f"Unsupported file extension now: {data_extension}"

    data_info = data_info_cls(
        resolved_data_path,
        vars_list,
        encoding=encoding,
        cache_dir=runtime.tmp_base_path,
        head=head,
    )
    try:
        return json.dumps(data_info.info, ensure_ascii=False)
    except Exception as error:
        logging.error(
            "Failed to serialize data summary for %s: %s",
            DataPathAuditor._safe_url_for_log(str(resolved_data_path)),
            error,
        )
        return f"Failed to generate data summary for {resolved_data_path}: {error}"


def get_data_info(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    config_file: str | Path | None = None,
) -> str:
    """Return descriptive statistics for a supported dataset."""
    return _get_data_info_impl(
        data_path=data_path,
        vars_list=vars_list,
        encoding=encoding,
        config_file=config_file,
    )
