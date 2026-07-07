#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : async_do.py

import asyncio
import logging
from pathlib import Path
from typing import Dict, Sequence

from ...utils import get_nowtime
from .do import StataDo


class AsyncStataDo(StataDo):
    """
    Async Stata do-file executor.

    This class keeps the synchronous StataDo behavior available through
    inheritance and adds coroutine-based entry points for concurrent execution.
    """

    async def execute_dofile_async(
        self,
        dofile_path: Path,
        log_file_name: str = None,
        is_replace: bool = True,
        enable_smcl: bool = True,
        timeout: float | None = None,
    ) -> Dict[str, Path]:
        """
        Execute one Stata do file asynchronously.

        Args:
            dofile_path: Path to do file.
            log_file_name: File name of log.
            is_replace: Whether to replace existing log files.
            enable_smcl: Whether to generate SMCL format log.
            timeout: Maximum execution time in seconds. None means no timeout.

        Returns:
            Dict[str, Path]: Generated log file paths.
        """
        if self.IS_MONITOR or not self.is_unix:
            return await asyncio.to_thread(
                self.execute_dofile,
                dofile_path,
                log_file_name,
                is_replace,
                enable_smcl,
                timeout,
            )

        timeout = self._validate_timeout(timeout)
        log_name = log_file_name or get_nowtime()
        self._validate_log_name(log_name)
        validated_dofile_path = self._validate_dofile_path(dofile_path)

        return await self._execute_unix_like_async(
            validated_dofile_path,
            log_name,
            is_replace,
            enable_smcl,
            timeout,
        )

    async def execute_dofiles(
        self,
        dofile_paths: Sequence[Path],
        log_file_names: Sequence[str] | None = None,
        is_replace: bool = True,
        enable_smcl: bool = True,
        timeout: float | None = None,
        max_concurrency: int | None = None,
    ) -> list[Dict[str, Path]]:
        """
        Execute multiple Stata do files concurrently.

        Args:
            dofile_paths: Paths to do files.
            log_file_names: Optional log names matching dofile_paths.
            is_replace: Whether to replace existing log files.
            enable_smcl: Whether to generate SMCL format log.
            timeout: Maximum execution time per do file. None means no timeout.
            max_concurrency: Maximum number of Stata processes at once.

        Returns:
            list[Dict[str, Path]]: Generated log file paths in input order.
        """
        paths = list(dofile_paths)
        if not paths:
            return []

        concurrency = self._validate_max_concurrency(max_concurrency, len(paths))
        if self.IS_MONITOR and concurrency > 1:
            raise RuntimeError(
                "Parallel execution with shared monitors is not supported. "
                "Use max_concurrency=1 or create isolated executors per task."
            )

        log_names = self._prepare_log_names(log_file_names, len(paths))
        semaphore = asyncio.Semaphore(concurrency)

        async def run_one(index: int, dofile_path: Path) -> Dict[str, Path]:
            async with semaphore:
                return await self.execute_dofile_async(
                    dofile_path=dofile_path,
                    log_file_name=log_names[index],
                    is_replace=is_replace,
                    enable_smcl=enable_smcl,
                    timeout=timeout,
                )

        tasks = [run_one(index, path) for index, path in enumerate(paths)]
        return await asyncio.gather(*tasks)

    async def _execute_unix_like_async(
        self,
        dofile_path: Path,
        log_name: str,
        is_replace: bool = True,
        enable_smcl: bool = True,
        timeout: float | None = None,
    ) -> Dict[str, Path]:
        """Execute Stata on macOS/Linux systems using asyncio subprocesses."""
        env = self.set_fake_terminal_size_env()
        proc = await asyncio.create_subprocess_exec(
            self.STATA_CLI,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=self.cwd,
        )

        try:
            log_file = self.generate_log_file(log_name)
            smcl_file = self.generate_log_file(log_name, 'smcl')
            commands = f"""
            capture log close
            {self.generate_log_command(log_file, is_replace)}
            {self.generate_log_command(smcl_file, is_replace, 'smcl') if enable_smcl else ''}
            do "{dofile_path}"
            log close _all
            clear
            exit, STATA
            """

            _, stderr = await asyncio.wait_for(
                proc.communicate(input=commands.encode("utf-8")),
                timeout=timeout,
            )
            stderr_text = stderr.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                logging.error(f"Stata execution failed: {stderr_text}")
                raise RuntimeError(f"Something went wrong: {stderr_text}")

            logging.info(f"Stata execution completed successfully. Log file: {log_file}")
            log_path_mapping = {"text": log_file}
            if enable_smcl:
                log_path_mapping["smcl"] = smcl_file
            return log_path_mapping
        except asyncio.TimeoutError as error:
            logging.warning(f"Stata execution timed out after {timeout:g} seconds")
            raise self._timeout_error(timeout) from error
        finally:
            await self._cleanup_async_process(proc)

    @staticmethod
    async def _cleanup_async_process(proc: asyncio.subprocess.Process | None) -> None:
        """Ensure an asyncio subprocess is terminated and reaped."""
        if proc is None or proc.returncode is not None:
            return

        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()

    @staticmethod
    def _validate_max_concurrency(
        max_concurrency: int | None,
        task_count: int,
    ) -> int:
        """Validate and normalize the concurrency limit."""
        if max_concurrency is None:
            return task_count
        if isinstance(max_concurrency, bool) or not isinstance(max_concurrency, int):
            raise ValueError("max_concurrency must be a positive integer or None.")
        if max_concurrency <= 0:
            raise ValueError("max_concurrency must be a positive integer or None.")
        return min(max_concurrency, task_count)

    def _prepare_log_names(
        self,
        log_file_names: Sequence[str] | None,
        task_count: int,
    ) -> list[str]:
        """Prepare one validated log name per task."""
        if log_file_names is not None:
            names = list(log_file_names)
            if len(names) != task_count:
                raise ValueError("log_file_names must match the number of dofile_paths.")
        else:
            nowtime = get_nowtime()
            names = [f"{nowtime}_{index + 1}" for index in range(task_count)]

        for name in names:
            self._validate_log_name(name)
        if len(set(names)) != len(names):
            raise ValueError("log_file_names must be unique for parallel execution.")
        return names
