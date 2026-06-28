#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : read_smcl.py

import re
from pathlib import Path

from .base import StataLogBase, StataLogInfo


MAX_SMCL_EXPANSION = 10_000


class StataLogSMCL(StataLogBase):
    """This class is made by Claude Code"""
    """Processor for SMCL (.smcl) Stata log files."""

    # 简单格式标签（直接移除）
    SIMPLE_TAGS = [
        'smcl', 'txt', 'res', 'com', 'err', 'inp',
        'sf', 'it', 'bf', 'ul on', 'ul off', '.-', 'right', 'center', 'bind'
    ]

    # 编译后的正则模式
    _SIMPLE_TAG_PATTERN = re.compile(
        r'\{(' + '|'.join(re.escape(tag) for tag in SIMPLE_TAGS) + r')\}'
    )
    _CLOSE_TAG_PATTERN = re.compile(r'\{/[\w\s]+\}')
    _HLINE_PATTERN = re.compile(r'\{hline\s*(\d*)\}')
    _SPACE_PATTERN = re.compile(r'\{space\s*(\d+)\}')
    _COL_PATTERN = re.compile(r'\{col\s*(\d+)\}')
    _P_PATTERN = re.compile(r'\{p\s*[\d\s]*\}|\{p_end\}')
    _C_CHAR_PATTERN = re.compile(r'\{c\s+(\w+)\}')
    _BROWSE_PATTERN = re.compile(r'\{browse\s+"([^"]+)":([^}]*)\}')
    _STATA_CMD_PATTERN = re.compile(r'\{stata\s+"([^"]+)":([^}]*)\}')

    # 框架行模式
    FRAMEWORK_PATTERNS = [
        r'^-+$',
        r'^\s*name:\s*\w+',
        r'^\s*log:\s*.+',
        r'^\s*log\s+type:\s*\w+',
        r'^\s*opened\s+on:\s*.+',
        r'^\s*closed\s+on:\s*.+',
        r'^\.\s*log\s+using\s+"[^"]+".*',
        r'^\.\s*do\s+"[^"]+\.do"\s*$',
        r'^end\s+of\s+do-file\s*$',
        r'^\.\s*log\s+close\s*_?\w*\s*$',
    ]
    _COMPILED_FRAMEWORK_PATTERNS = [re.compile(p) for p in FRAMEWORK_PATTERNS]

    # 命令行模式
    COMMAND_PATTERN = re.compile(r'^\.\s+(.+)$')

    # 续行模式
    CONTINUATION_PATTERN = re.compile(r'^>')

    @staticmethod
    def _bounded_count(value: str | None, default: int) -> int:
        """Return a safe SMCL expansion count."""
        if not value:
            return default
        return min(int(value), MAX_SMCL_EXPANSION)

    def _convert_to_dataclass(self) -> StataLogInfo:
        """
        Parse SMCL log file into StataLogInfo.

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

    def read_without_framework(self) -> str:
        """
        Convert SMCL to plain text and remove framework content.

        Returns:
            str: Clean plain text log content.
        """
        content = self.read_plain_text()
        text = self._strip_smcl_tags(content)
        text = self._remove_framework(text)
        text = self._clean_format(text)
        return text

    def _strip_smcl_tags(self, content: str) -> str:
        """
        Remove SMCL formatting tags, returning plain text.

        Args:
            content: Raw SMCL content

        Returns:
            str: Plain text with SMCL tags removed
        """
        result = content

        # 处理 hline
        result = self._HLINE_PATTERN.sub(
            lambda m: '-' * self._bounded_count(m.group(1), 13),
            result
        )

        # 处理 space
        result = self._SPACE_PATTERN.sub(
            lambda m: ' ' * self._bounded_count(m.group(1), 0),
            result
        )

        # 处理 col（简化处理，移除）
        result = self._COL_PATTERN.sub('', result)

        # 处理 p 标签
        result = self._P_PATTERN.sub('', result)

        # 处理表格边框字符
        result = self._C_CHAR_PATTERN.sub(
            lambda m: {'|': '|', '+': '+', 'TT': '+', 'BT': '+', 'TC': '+', 'BC': '+'}.get(m.group(1), '|'),
            result
        )

        # 处理链接（保留文本）
        result = self._BROWSE_PATTERN.sub(r'\2', result)
        result = self._STATA_CMD_PATTERN.sub(r'\2', result)

        # 移除简单标签
        result = self._SIMPLE_TAG_PATTERN.sub('', result)
        result = self._CLOSE_TAG_PATTERN.sub('', result)

        return result

    def _remove_framework(self, content: str) -> str:
        """Remove log header, footer, and framework commands."""
        lines = content.split('\n')
        filtered_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                filtered_lines.append(line)
                continue

            is_framework = False
            for pattern in self._COMPILED_FRAMEWORK_PATTERNS:
                if pattern.match(stripped):
                    is_framework = True
                    break

            if not is_framework:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def _clean_format(self, content: str) -> str:
        """Clean up formatting."""
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

    def _parse_command_results(self, content: str) -> list:
        """Parse content into command-result list."""
        lines = content.split('\n')
        result_list = []
        current_command = None
        current_result_lines = []

        for line in lines:
            # 处理续行（以 > 开头）
            if self.CONTINUATION_PATTERN.match(line):
                if current_command is not None:
                    # 合并续行到当前命令
                    current_command += line[1:].lstrip()
                continue

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
        match = re.search(r'\.\s*do\s+"([^"]+\.do)"', content)
        if match:
            return Path(match.group(1))
        return None
