#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : read_text.py

import re
from pathlib import Path

from .base import StataLogBase, StataLogInfo


class StataLogTEXT(StataLogBase):
    """Processor for plain text (.log) Stata log files."""

    # 框架行的正则模式列表
    FRAMEWORK_PATTERNS = [
        r'^-+$',
        r'^\s*name:\s*\w+',
        r'^\s*log:\s*.+',
        r'^\s*log\s+type:\s*\w+',
        r'^\s*opened\s+on:\s*.+',
        r'^\s*closed\s+on:\s*.+',
        r'^\.\s*log\s+using\s+"[^"]+".*',
        r'^\(file\b.*not found\)$',
        r'^\(file$',
        r'^\s*/.*not found\)$',
        r'^\s*/.*\.(smcl|log).+$',
        r'^\s*/.*stata-mcp.*$',
        r'^\s*>.*not found\)$',
        r'^\.\s*do\s+"[^"]+\.do"\s*$',
        r'^end\s+of\s+do-file\s*$',
        r'^\.\s*log\s+close\s*_?\w*\s*$',
    ]

    # 编译后的正则模式（类变量）
    _COMPILED_PATTERNS = [re.compile(p) for p in FRAMEWORK_PATTERNS]

    # 命令行模式（以 . 开头）
    COMMAND_PATTERN = re.compile(r'^\.\s+(.+)$')

    # 断行续行模式
    CONTINUATION_PATTERN = re.compile(r'^>')

    def _convert_to_dataclass(self) -> StataLogInfo:
        """
        Parse log file into StataLogInfo with command-result list.

        Returns:
            StataLogInfo: Parsed log information
        """
        clean_content = self.read_without_framework()
        command_result_list = self._parse_command_results(clean_content)
        do_file_path = self._extract_do_file_path()

        return StataLogInfo(
            log_file_path=self.log_file_path,
            command_result_list=command_result_list,
            do_file_path=do_file_path
        )

    def _parse_command_results(self, content: str) -> list:
        """
        Parse content into command-result list.

        A command line starts with '. ' and the result is everything
        until the next command line.

        Args:
            content: Clean log content without framework

        Returns:
            List of {"command": cmd, "result": res} dicts
        """
        lines = content.split('\n')
        result_list = []
        current_command = None
        current_result_lines = []

        for line in lines:
            cmd_match = self.COMMAND_PATTERN.match(line)
            if cmd_match:
                # 保存上一个命令的结果
                if current_command is not None:
                    result = '\n'.join(current_result_lines).strip()
                    result_list.append({
                        "command": current_command,
                        "result": result
                    })

                # 开始新命令
                current_command = cmd_match.group(1).strip()
                current_result_lines = []
            else:
                # 这是结果行
                if current_command is not None:
                    current_result_lines.append(line)

        # 保存最后一个命令的结果
        if current_command is not None:
            result = '\n'.join(current_result_lines).strip()
            result_list.append({
                "command": current_command,
                "result": result
            })

        return result_list

    def _extract_do_file_path(self):
        """
        Extract do-file path from log content.

        Returns:
            Path to do-file if found, None otherwise
        """
        content = self.read_plain_text()
        # 匹配 . do "path/to/file.do"
        match = re.search(r'\.\s*do\s+"([^"]+\.do)"', content)
        if match:
            return Path(match.group(1))
        return None

    def read_without_framework(self) -> str:
        """
        Remove framework content from TEXT log.

        Returns:
            str: Clean log content without framework elements.
        """
        content = self.read_plain_text()

        # Step 1: 合并断行
        lines = self._join_wrapped_lines(content)

        # Step 2: 过滤框架行
        filtered_lines = []
        for line in lines:
            if self._is_framework_line(line):
                continue
            filtered_lines.append(line)

        # Step 3: 清理多余空行
        result = '\n'.join(filtered_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()

    def _join_wrapped_lines(self, content: str) -> list:
        """Join wrapped lines (prefixed with '>')."""
        raw_lines = content.split('\n')
        merged_lines = []
        current_line = ""

        for line in raw_lines:
            if self.CONTINUATION_PATTERN.match(line):
                continuation = self.CONTINUATION_PATTERN.sub('', line)
                current_line += continuation
            else:
                if current_line:
                    merged_lines.append(current_line)
                current_line = line

        if current_line:
            merged_lines.append(current_line)

        return merged_lines

    def _is_framework_line(self, line: str) -> bool:
        """Check if a line is framework content."""
        stripped = line.strip()
        if not stripped:
            return False

        for pattern in self._COMPILED_PATTERNS:
            if pattern.match(stripped):
                return True
        return False
