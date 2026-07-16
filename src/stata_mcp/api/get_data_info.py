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
import time
from pathlib import Path
from typing import List

from .._diagnostic_logging import (
    elapsed_ms,
    log_event,
    new_request_id,
    safe_stack,
    source_reference,
    utf8_size,
)
from ..config import ToolContext
from ..data_info import get_data_handler
from ..guard.data_path_auditor import DataPathAuditor
from ._runtime import create_runtime_context

logger = logging.getLogger(__name__)


def _get_data_info_impl(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    config_file: str | Path | None = None,
    *,
    head: int | None = None,
    tool_context: ToolContext = "api",
    request_id: str | None = None,
) -> str:
    """Return descriptive statistics for a supported dataset."""
    active_request_id = request_id or new_request_id()
    started_at = time.perf_counter()
    source_ref = source_reference(data_path)
    requested_vars_count = len(vars_list) if vars_list is not None else 0
    summary_started = False
    log_event(
        logger,
        logging.INFO,
        "get_data_info.request.started",
        active_request_id,
        head=head,
        requested_vars_count=requested_vars_count,
        source_ref=source_ref,
    )

    try:
        stage_started_at = time.perf_counter()
        runtime = create_runtime_context(config_file=config_file)
        data_info_config = runtime.config.get_data_info_config(tool_context)
        resolved_head = data_info_config.heads if head is None else head
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.runtime.ready",
            active_request_id,
            cache_enabled=data_info_config.is_cache,
            duration_ms=elapsed_ms(stage_started_at),
        )
        auditor = DataPathAuditor(
            working_dir=runtime.config.WORKING_DIR,
            strict_local_boundary=runtime.config.STRICT_DATA_INFO_LOCAL_BOUNDARY,
            enable_url_guard=runtime.config.ENABLE_DATA_INFO_URL_GUARD,
            allowed_url_domains=runtime.config.DATA_INFO_ALLOWED_URL_DOMAINS,
        )

        stage_started_at = time.perf_counter()
        source_kind = "url" if auditor.is_url(data_path) else "local"
        if source_kind == "url":
            validated_data = auditor.validate_url(data_path)
            if not isinstance(validated_data, tuple):
                log_event(
                    logger,
                    logging.WARNING,
                    "get_data_info.path.rejected",
                    active_request_id,
                    duration_ms=elapsed_ms(stage_started_at),
                    source_kind=source_kind,
                    source_ref=source_ref,
                )
                log_event(
                    logger,
                    logging.INFO,
                    "get_data_info.request.completed",
                    active_request_id,
                    duration_ms=elapsed_ms(started_at),
                    outcome="path_rejected",
                )
                return validated_data
            resolved_data_path, data_extension = validated_data
        else:
            validated_data_path = auditor.validate_local_path(data_path)
            if isinstance(validated_data_path, str):
                log_event(
                    logger,
                    logging.WARNING,
                    "get_data_info.path.rejected",
                    active_request_id,
                    duration_ms=elapsed_ms(stage_started_at),
                    source_kind=source_kind,
                    source_ref=source_ref,
                )
                log_event(
                    logger,
                    logging.INFO,
                    "get_data_info.request.completed",
                    active_request_id,
                    duration_ms=elapsed_ms(started_at),
                    outcome="path_rejected",
                )
                return validated_data_path
            resolved_data_path = validated_data_path
            data_extension = resolved_data_path.suffix.lower().strip(".")
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.path.validated",
            active_request_id,
            duration_ms=elapsed_ms(stage_started_at),
            source_kind=source_kind,
            source_ref=source_ref,
            resolved_source_ref=source_reference(resolved_data_path),
            suffix=data_extension,
        )

        data_info_cls = get_data_handler(data_extension)
        if not data_info_cls:
            log_event(
                logger,
                logging.WARNING,
                "get_data_info.handler.unsupported",
                active_request_id,
                suffix=data_extension,
            )
            log_event(
                logger,
                logging.INFO,
                "get_data_info.request.completed",
                active_request_id,
                duration_ms=elapsed_ms(started_at),
                outcome="unsupported_extension",
            )
            return f"Unsupported file extension now: {data_extension}"

        stage_started_at = time.perf_counter()
        data_info = data_info_cls(
            resolved_data_path,
            vars_list,
            encoding=encoding,
            cache_dir=runtime.tmp_base_path,
            head=resolved_head,
            is_cache=data_info_config.is_cache,
            metrics=data_info_config.metrics,
            string_keep_number=data_info_config.string_keep_number,
            decimal_places=data_info_config.decimal_places,
            hash_length=data_info_config.hash_length,
            request_id=active_request_id,
        )
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.handler.initialized",
            active_request_id,
            duration_ms=elapsed_ms(stage_started_at),
            handler=data_info_cls.__name__,
        )

        stage_started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.info.started",
            active_request_id,
        )
        summary_started = True
        data_summary = data_info.info
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.info.completed",
            active_request_id,
            duration_ms=elapsed_ms(stage_started_at),
        )

        stage_started_at = time.perf_counter()
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.serialization.started",
            active_request_id,
        )
        result = json.dumps(data_summary, ensure_ascii=False)
        result_utf8_bytes = utf8_size(result)
        log_event(
            logger,
            logging.DEBUG,
            "get_data_info.serialization.completed",
            active_request_id,
            duration_ms=elapsed_ms(stage_started_at),
            result_chars=len(result),
            tool_result_utf8_bytes=result_utf8_bytes,
        )
        log_event(
            logger,
            logging.INFO,
            "get_data_info.request.completed",
            active_request_id,
            duration_ms=elapsed_ms(started_at),
            outcome="success",
            tool_result_utf8_bytes=result_utf8_bytes,
        )
        return result
    except Exception as error:
        log_event(
            logger,
            logging.ERROR,
            "get_data_info.request.failed",
            active_request_id,
            duration_ms=elapsed_ms(started_at),
            error_type=type(error).__name__,
            source_ref=source_ref,
        )
        log_event(
            logger,
            logging.ERROR,
            "get_data_info.request.stack",
            active_request_id,
            stack=safe_stack(error),
        )
        if summary_started:
            return f"Failed to generate data summary for {resolved_data_path}: {error}"
        raise


def get_data_info(
    data_path: str,
    vars_list: List[str] | None = None,
    encoding: str = "utf-8",
    config_file: str | Path | None = None,
    *,
    head: int | None = None,
    tool_context: ToolContext = "api",
) -> str:
    """Return descriptive statistics for a supported dataset."""
    return _get_data_info_impl(
        data_path=data_path,
        vars_list=vars_list,
        encoding=encoding,
        config_file=config_file,
        head=head,
        tool_context=tool_context,
    )
