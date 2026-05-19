#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : do.py

import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Literal, Optional

from ...utils import get_nowtime

LOG_FILE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


class StataDo:
    def __init__(self,
                 stata_cli: str,
                 log_file_path: Path,
                 is_unix: bool = None,
                 cwd: Path = None,
                 monitors: Optional[List] = None):
        """
        Initialize Stata executor

        Args:
            stata_cli: Path to Stata command line tool
            log_file_path: Path for storing log files
            is_unix: Whether the OS is Unix-like (macOS/Linux)
            cwd (Path): current working directory
            monitors: List of monitor instances (e.g., RAMMonitor, TimeoutMonitor)
        """
        self.stata_cli = stata_cli
        self.log_file_path = log_file_path
        if is_unix is not None:
            self.is_unix = is_unix
        else:
            from ...utils import get_os
            self.is_unix = get_os() in ["Darwin", "Linux"]
        self.cwd = cwd or Path.cwd()
        self.monitors = monitors or []
        self.IS_MONITOR = len(self.monitors) > 0

    def set_cli(self, cli_path):
        self.stata_cli = cli_path

    @property
    def STATA_CLI(self):
        return self.stata_cli

    def execute_dofile(
        self,
        dofile_path: Path,
        log_file_name: str = None,
        is_replace: bool = True,
        enable_smcl: bool = True
    ) -> Dict[str, Path]:
        """
        Execute Stata do file and return log file path

        Args:
            dofile_path (Path): Path to do file
            log_file_name (str, optional): File name of log
            is_replace (bool): Whether replace the log file if exists before. Default is True
            enable_smcl (bool): Whether enable .smcl format log. Default is True

        Returns:
            Dict[str, Path]: Dictionary of generated log file paths.
                - "text": .log file path (always present)
                - "smcl": .smcl file path (present if enable_smcl is True)

        Raises:
            ValueError: Unsupported operating system
            RuntimeError: Stata execution error
        """
        nowtime = get_nowtime()
        log_name = log_file_name or nowtime
        self._validate_log_name(log_name)
        dofile_path = self._validate_dofile_path(dofile_path)
        log_file = self.generate_log_file(log_name)

        if self.is_unix:
            args = dofile_path, log_name, is_replace, enable_smcl
            if self.IS_MONITOR:
                return self._execute_unix_like_with_monitors(*args)
            else:
                return self._execute_unix_like(*args)
        else:
            # As I do not have a Windows device, I can't test this feature.
            # Therefore, Windows is not supported yet.
            if self.IS_MONITOR:
                self._execute_windows_with_monitors(dofile_path, log_file, is_replace)
            else:
                self._execute_windows(dofile_path, log_file, is_replace)

        return {"text": log_file}

    @staticmethod
    def set_fake_terminal_size_env(columns: str | int = '120',
                                   lines: str | int = '40') -> Dict[str, str]:
        env = os.environ.copy()
        env['COLUMNS'] = str(columns)
        env['LINES'] = str(lines)
        return env

    @staticmethod
    def _cleanup_process(proc: Optional[subprocess.Popen]) -> None:
        """
        Ensure subprocess is terminated and reaped to prevent resource leaks.

        Args:
            proc: The subprocess to clean up, or None if not created
        """
        if proc is None:
            return
        if proc.poll() is None:  # Process still running
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    @staticmethod
    def generate_log_command(log_file: Path, is_replace: bool = True, log_type: Literal['smcl', 'text'] = 'text'):
        replace_clause = 'replace' if is_replace else ''
        log_cmd = f'log using "{log_file.as_posix()}", {replace_clause} {log_type} name({log_type}_log)'
        return log_cmd

    @staticmethod
    def _validate_log_name(log_name: str) -> None:
        if not LOG_FILE_NAME_PATTERN.fullmatch(log_name):
            raise ValueError(
                "Invalid log_file_name. Use 1-128 characters from A-Z, a-z, 0-9, underscore, dot, or hyphen."
            )
        if log_name in {"", ".", ".."}:
            raise ValueError("Invalid log_file_name. Path traversal is not allowed.")

    @staticmethod
    def _validate_dofile_path(dofile_path: Path) -> Path:
        resolved_path = Path(dofile_path).resolve()
        if resolved_path.suffix.lower() != ".do":
            raise ValueError("Invalid dofile_path. Only .do files are allowed.")

        path_text = resolved_path.as_posix()
        if any(char in path_text for char in ('"', "'", "`", "\n", "\r")):
            raise ValueError("Invalid dofile_path. Quotes, backticks, and newlines are not allowed.")

        return resolved_path

    def generate_log_file(self, log_name: str, extension: Literal['smcl', 'log'] = 'log'):
        log_root = self.log_file_path.resolve()
        log_file = (self.log_file_path / f"{log_name}.{extension}").resolve()
        if not log_file.is_relative_to(log_root):
            raise ValueError("Invalid log_file_name. Path traversal is not allowed.")
        return log_file

    def _execute_unix_like(
        self,
        dofile_path: Path,
        log_name: str,
        is_replace: bool = True,
        enable_smcl: bool = True
    ) -> Dict[str, Path]:
        """
        Execute Stata on macOS/Linux systems

        Args:
            dofile_path: Path to do file
            log_name: name of log file
            is_replace: Whether replace the log file if exists.
            enable_smcl: Whether to generate SMCL format log.

        Returns:
            Dict[str, Path]: Dictionary of generated log file paths.
                - "text": .log file path (always present)
                - "smcl": .smcl file path (present if enable_smcl is True)

        Raises:
            RuntimeError: Stata execution error
        """
        # Get environment with terminal size settings
        env = self.set_fake_terminal_size_env()

        proc = subprocess.Popen(
            [self.STATA_CLI],  # Launch the Stata CLI
            stdin=subprocess.PIPE,  # Prepare to send commands
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,  # Direct execution, subprocess handles path spaces safely
            env=env,  # Use environment with terminal size settings
            cwd=self.cwd  # Set cwd for more friendly control output
        )

        try:
            # Execute commands sequentially in Stata
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
            _, stderr = proc.communicate(input=commands)  # Send commands and wait for completion

            if proc.returncode != 0:
                logging.error(f"Stata execution failed: {stderr}")
                raise RuntimeError(f"Something went wrong: {stderr}")
            else:
                logging.info(f"Stata execution completed successfully. Log file: {log_file}")

            log_path_mapping = {"text": log_file}
            if enable_smcl:
                log_path_mapping["smcl"] = smcl_file
            return log_path_mapping
        finally:
            self._cleanup_process(proc)

    def _execute_windows(self, dofile_path: Path, log_file: Path, is_replace: bool = True):
        """
        Execute Stata on Windows systems

        Args:
            dofile_path: Path to do file
            log_file: Path to log file
            is_replace: Whether replace the log file if exists.
        """
        # Windows approach - use the /e flag to run a batch command
        # Create a temporary batch file in system temp directory
        batch_file = Path(tempfile.gettempdir()) / f"stata_batch__{dofile_path.stem}.do"

        replace_clause = ", replace" if is_replace else ""
        try:
            with open(batch_file, "w", encoding="utf-8") as f:
                f.write("capture log close\n")
                f.write(f'log using "{log_file}"{replace_clause}\n')
                f.write(f'do "{dofile_path}"\n')
                f.write("log close\n")
                f.write("exit, STATA\n")

            # Run Stata on Windows using /e to execute the batch file
            cmd = [self.STATA_CLI, "/e", "do", batch_file.as_posix()]
            result = subprocess.run(
                cmd,
                shell=True,  # Windows Stata requires shell execution for proper path resolution and startup
                capture_output=True,
                text=True,
                cwd=self.cwd
            )
            if result.returncode != 0:
                logging.error(f"Stata execution failed on Windows: {result.stderr}")
                raise RuntimeError(f"Windows Stata execution failed: {result.stderr}")
            else:
                logging.info(f"Stata execution completed successfully on Windows. Log file: {log_file}")

        except Exception as e:
            logging.error(f"Error during Windows Stata execution: {str(e)}")
            raise
        finally:
            # Clean up temporary batch file
            if batch_file.exists():
                try:
                    batch_file.unlink()
                    logging.debug(f"Temporary batch file removed: {batch_file}")
                except Exception as e:
                    logging.warning(f"Failed to remove temporary batch file {batch_file}: {str(e)}")

    def _execute_unix_like_with_monitors(
        self,
        dofile_path: Path,
        log_name: str,
        is_replace: bool = True,
        enable_smcl: bool = True
    ) -> Dict[str, Path]:
        """
        Execute Stata on macOS/Linux systems with monitoring enabled.

        Args:
            dofile_path: Path to do file
            log_name: name of log file
            is_replace: Whether replace the log file if exists.
            enable_smcl: Whether to generate SMCL format log.

        Returns:
            Dict[str, Path]: Dictionary of generated log file paths.
                - "text": .log file path (always present)
                - "smcl": .smcl file path (present if enable_smcl is True)

        Raises:
            RuntimeError: Stata execution error
        """
        # Get environment with terminal size settings
        env = self.set_fake_terminal_size_env()

        proc = subprocess.Popen(
            [self.STATA_CLI],  # Launch the Stata CLI
            stdin=subprocess.PIPE,  # Prepare to send commands
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,  # Direct execution, subprocess handles path spaces safely
            env=env,  # Use environment with terminal size settings
            cwd=self.cwd  # Set cwd for more friendly control output
        )

        try:
            # Execute commands sequentially in Stata
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

            # Start all monitors
            if self.monitors:
                logging.info(f"Starting {len(self.monitors)} monitor(s)")
            for monitor in self.monitors:
                monitor.start(proc)

            _, stderr = proc.communicate(input=commands)  # Send commands and wait for completion

            if proc.returncode != 0:
                logging.error(f"Stata execution failed: {stderr}")
                raise RuntimeError(f"Something went wrong: {stderr}")
            else:
                logging.info(f"Stata execution completed successfully. Log file: {log_file}")

            generated_log_paths = {"text": log_file}
            if enable_smcl:
                generated_log_paths["smcl"] = smcl_file
            return generated_log_paths
        finally:
            # Stop monitors first
            for monitor in self.monitors:
                try:
                    monitor.stop()
                except Exception as e:
                    logging.warning(f"Monitor stop failed: {e}")
            # Then cleanup process
            self._cleanup_process(proc)

    def _execute_windows_with_monitors(self, dofile_path: Path, log_file: Path, is_replace: bool = True):
        """
        Execute Stata on Windows systems with monitoring enabled.

        Args:
            dofile_path: Path to do file
            log_file: Path to log file
            is_replace: Whether replace the log file if exists.

        Raises:
            RuntimeError: Stata execution error
        """
        # Windows approach - use the /e flag to run a batch command
        # Create a temporary batch file in system temp directory
        batch_file = Path(tempfile.gettempdir()) / f"stata_batch__{dofile_path.stem}.do"
        proc: Optional[subprocess.Popen] = None

        replace_clause = ", replace" if is_replace else ""
        try:
            with open(batch_file, "w", encoding="utf-8") as f:
                f.write("capture log close\n")
                f.write(f'log using "{log_file}"{replace_clause}\n')
                f.write(f'do "{dofile_path}"\n')
                f.write("log close\n")
                f.write("exit, STATA\n")

            # Run Stata on Windows using /e to execute the batch file
            # Use Popen instead of run to enable monitoring
            cmd = [self.STATA_CLI, "/e", "do", str(batch_file)]
            proc = subprocess.Popen(
                cmd,
                shell=True,  # Windows Stata requires shell execution for proper path resolution and startup
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.cwd
            )

            # Start all monitors
            if self.monitors:
                logging.info(f"Starting {len(self.monitors)} monitor(s) on Windows")
            for monitor in self.monitors:
                monitor.start(proc)

            # Wait for process to complete
            _, stderr = proc.communicate()

            if proc.returncode != 0:
                logging.error(f"Stata execution failed on Windows: {stderr}")
                raise RuntimeError(f"Windows Stata execution failed: {stderr}")
            else:
                logging.info(f"Stata execution completed successfully on Windows. Log file: {log_file}")

        except RuntimeError:
            # Re-raise RuntimeError (includes monitor errors)
            raise
        except Exception as e:
            logging.error(f"Error during Windows Stata execution: {str(e)}")
            raise RuntimeError(f"Windows Stata execution error: {str(e)}")
        finally:
            # Stop monitors first
            for monitor in self.monitors:
                try:
                    monitor.stop()
                except Exception as e:
                    logging.warning(f"Monitor stop failed: {e}")
            # Cleanup process
            self._cleanup_process(proc)
            # Clean up temporary batch file
            if batch_file.exists():
                try:
                    batch_file.unlink()
                    logging.debug(f"Temporary batch file removed: {batch_file}")
                except Exception as e:
                    logging.warning(f"Failed to remove temporary batch file {batch_file}: {str(e)}")

    @staticmethod
    def read_log(log_file_path, mode="r", encoding="utf-8") -> str:
        try:
            with open(log_file_path, mode, encoding=encoding) as file:
                log_content = file.read()
            return log_content
        except Exception as e:
            return f"Failed to read logfile-{log_file_path}: {e}"
