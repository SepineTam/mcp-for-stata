#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : do.py

import logging
import math
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Literal, Optional
from uuid import uuid4

from ...audit import (
    AuditExecutionContext,
    AuditStore,
    current_audit_context,
)
from ...observability import debug_step
from ...utils import get_nowtime

LOG_FILE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


class StataDo:
    def __init__(self,
                 stata_cli: str,
                 log_file_path: Path,
                 is_unix: bool = None,
                 cwd: Path = None,
                 monitors: Optional[List] = None,
                 audit_store: AuditStore | None = None,
                 audit_interface: str = "runtime"):
        """
        Initialize Stata executor

        Args:
            stata_cli: Path to Stata command line tool
            log_file_path: Path for storing log files
            is_unix: Whether the OS is Unix-like (macOS/Linux)
            cwd (Path): current working directory
            monitors: List of monitor instances (e.g., RAMMonitor, TimeoutMonitor)
            audit_store: Optional audit store. Defaults to the log artifact root.
            audit_interface: Interface label for standalone audit events.
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
        self.audit_store = audit_store or AuditStore(
            self._default_audit_base_path(log_file_path)
        )
        self.audit_interface = audit_interface

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
        enable_smcl: bool = True,
        timeout: float | None = None,
    ) -> Dict[str, Path]:
        """
        Execute Stata do file and return log file path

        Args:
            dofile_path (Path): Path to do file
            log_file_name (str, optional): File name of log
            is_replace (bool): Whether replace the log file if exists before. Default is True
            enable_smcl (bool): Whether enable .smcl format log. Default is True
            timeout: Maximum execution time in seconds. None means no timeout.

        Returns:
            Dict[str, Path]: Dictionary of generated log file paths.
                - "text": .log file path (always present)
                - "smcl": .smcl file path (present if enable_smcl is True)

        Raises:
            ValueError: Unsupported operating system
            RuntimeError: Stata execution error
        """
        with debug_step("stata_do.input_validation", tool="stata_do"):
            timeout = self._validate_timeout(timeout)
            nowtime = get_nowtime()
            log_name = log_file_name or nowtime
            self._validate_log_name(log_name)
            dofile_path = self._validate_dofile_path(dofile_path)
            log_file = self.generate_log_file(log_name)

        execution_path, audit_context, owns_run = self._begin_audited_execution(
            dofile_path,
            log_name,
            is_replace,
            enable_smcl,
            timeout,
        )

        try:
            with debug_step(
                "stata_do.process_execution",
                tool="stata_do",
                run_id=audit_context.run.run_id,
                attributes={"mode": "sync", "platform": "unix" if self.is_unix else "windows"},
            ):
                if self.is_unix:
                    if self.IS_MONITOR:
                        result = self._execute_unix_like_with_monitors(
                            execution_path,
                            log_name,
                            is_replace,
                            enable_smcl,
                            timeout,
                        )
                    else:
                        result = self._execute_unix_like(
                            execution_path,
                            log_name,
                            is_replace,
                            enable_smcl,
                            timeout,
                        )
                else:
                    if self.IS_MONITOR:
                        self._execute_windows_with_monitors(
                            execution_path,
                            log_file,
                            is_replace,
                            timeout,
                        )
                    else:
                        self._execute_windows(
                            execution_path,
                            log_file,
                            is_replace,
                            timeout,
                        )
                    result = {"text": log_file}
        except BaseException as error:
            with debug_step(
                "stata_do.audit_finalize",
                tool="stata_do",
                run_id=audit_context.run.run_id,
                attributes={"outcome": "failed"},
            ):
                self._finish_audited_failure(audit_context, owns_run, error)
            raise

        with debug_step(
            "stata_do.audit_finalize",
            tool="stata_do",
            run_id=audit_context.run.run_id,
            attributes={"outcome": "completed"},
        ):
            self._finish_audited_success(audit_context, owns_run, result)
        return result

    @staticmethod
    def _default_audit_base_path(log_file_path: Path) -> Path:
        """Derive the project artifact root from the configured log directory."""
        normalized_path = Path(log_file_path)
        if normalized_path.name in {"stata-mcp-log", "log", "logs"}:
            return normalized_path.parent
        return normalized_path

    def _begin_audited_execution(
        self,
        dofile_path: Path,
        log_name: str,
        is_replace: bool,
        enable_smcl: bool,
        timeout: float | None,
    ) -> tuple[Path, AuditExecutionContext, bool]:
        """Create or reuse an audit run and snapshot the exact source."""
        audit_context = current_audit_context()
        owns_run = audit_context is None or audit_context.run.tool != "stata_do"
        if owns_run:
            run = self.audit_store.start_run(
                tool="stata_do",
                source_reference=dofile_path.as_posix(),
                input_payload={
                    "dofile_path": dofile_path.as_posix(),
                    "log_file_name": log_name,
                    "is_replace_log": is_replace,
                    "enable_smcl": enable_smcl,
                    "timeout": timeout,
                },
                interface=self.audit_interface,
            )
            audit_context = AuditExecutionContext(run=run, store=self.audit_store)

        assert audit_context is not None
        try:
            with debug_step(
                "stata_do.snapshot",
                tool="stata_do",
                run_id=audit_context.run.run_id,
            ):
                snapshot = audit_context.store.snapshot_dofile(
                    audit_context.run,
                    dofile_path,
                )
        except BaseException as error:
            if owns_run:
                audit_context.store.finish_run(
                    audit_context.run,
                    event="failed",
                    error={
                        "type": type(error).__name__,
                        "message": str(error),
                        "phase": "snapshot",
                    },
                )
            raise

        audit_context.artifacts.update(
            {
                "snapshot_path": snapshot.path.as_posix(),
                "snapshot_sha256": snapshot.sha256,
                "snapshot_reused": snapshot.reused,
            }
        )
        return snapshot.path, audit_context, owns_run

    @staticmethod
    def _finish_audited_success(
        audit_context: AuditExecutionContext,
        owns_run: bool,
        log_paths: Dict[str, Path],
    ) -> None:
        audit_context.artifacts.update(
            {
                f"{log_type}_log_path": log_path.as_posix()
                for log_type, log_path in log_paths.items()
            }
        )
        if owns_run:
            audit_context.store.finish_run(
                audit_context.run,
                event="completed",
                artifacts=audit_context.artifacts,
            )

    @staticmethod
    def _finish_audited_failure(
        audit_context: AuditExecutionContext,
        owns_run: bool,
        error: BaseException,
    ) -> None:
        if not owns_run:
            return
        if isinstance(error, KeyboardInterrupt):
            event = "interrupted"
        elif "timed out" in str(error).lower():
            event = "timeout"
        else:
            event = "failed"
        audit_context.store.finish_run(
            audit_context.run,
            event=event,
            artifacts=audit_context.artifacts,
            error={
                "type": type(error).__name__,
                "message": str(error),
                "phase": "execution",
            },
        )

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
                logging.warning("Stata process did not terminate; killed")
                proc.kill()
                proc.wait()

    @staticmethod
    def _validate_timeout(timeout: float | None) -> float | None:
        """Validate and normalize an optional execution timeout."""
        if timeout is None:
            return None
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise ValueError(
                "Invalid timeout. Use a positive, finite number of seconds or None."
            )
        try:
            normalized_timeout = float(timeout)
        except OverflowError as error:
            raise ValueError(
                "Invalid timeout. Use a positive, finite number of seconds or None."
            ) from error
        if not math.isfinite(normalized_timeout) or normalized_timeout <= 0:
            raise ValueError(
                "Invalid timeout. Use a positive, finite number of seconds or None."
            )
        return normalized_timeout

    @staticmethod
    def _timeout_error(timeout: float) -> RuntimeError:
        """Build a consistent Stata execution timeout error."""
        return RuntimeError(f"Stata execution timed out after {timeout:g} seconds.")

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

    @staticmethod
    def _generate_batch_file_name() -> str:
        """Random batch filename for the Windows launcher.

        The name must never be derived from user-controlled input (e.g. the
        do-file stem): the batch path is passed to a shell on Windows, so any
        metacharacter smuggled into the filename would be interpreted there.
        """
        return f"stata_batch__{uuid4().hex}.do"

    @classmethod
    def _create_windows_batch_file(
        cls,
        dofile_path: Path,
        log_file: Path,
        is_replace: bool,
    ) -> Path:
        """Atomically create and write a random Windows wrapper do-file."""
        batch_prefix = Path(cls._generate_batch_file_name()).stem
        replace_clause = ", replace" if is_replace else ""
        batch_file: Optional[Path] = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                prefix=f"{batch_prefix}__",
                suffix=".do",
                delete=False,
                newline="\n",
            ) as file:
                batch_file = Path(file.name)
                file.write("capture log close\n")
                file.write(f'log using "{log_file}"{replace_clause}\n')
                file.write(f'do "{dofile_path}"\n')
                file.write("log close\n")
                file.write("exit, STATA\n")
        except Exception:
            if batch_file is not None:
                try:
                    batch_file.unlink(missing_ok=True)
                except OSError as error:
                    logging.warning(
                        "Failed to remove incomplete temporary batch file %s: %s",
                        batch_file,
                        error,
                    )
            raise

        assert batch_file is not None
        return batch_file

    def _execute_unix_like(
        self,
        dofile_path: Path,
        log_name: str,
        is_replace: bool = True,
        enable_smcl: bool = True,
        timeout: float | None = None,
    ) -> Dict[str, Path]:
        """
        Execute Stata on macOS/Linux systems

        Args:
            dofile_path: Path to do file
            log_name: name of log file
            is_replace: Whether replace the log file if exists.
            enable_smcl: Whether to generate SMCL format log.
            timeout: Maximum execution time in seconds. None means no timeout.

        Returns:
            Dict[str, Path]: Dictionary of generated log file paths.
                - "text": .log file path (always present)
                - "smcl": .smcl file path (present if enable_smcl is True)

        Raises:
            RuntimeError: Stata execution error
        """
        # Get environment with terminal size settings
        env = self.set_fake_terminal_size_env()

        logging.info("Launching Stata %s in cwd %s", self.STATA_CLI, self.cwd)
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
            _, stderr = proc.communicate(input=commands, timeout=timeout)

            if proc.returncode != 0:
                logging.error(f"Stata execution failed: {stderr}")
                raise RuntimeError(f"Something went wrong: {stderr}")
            else:
                logging.info(f"Stata execution completed successfully. Log file: {log_file}")

            log_path_mapping = {"text": log_file}
            if enable_smcl:
                log_path_mapping["smcl"] = smcl_file
            return log_path_mapping
        except subprocess.TimeoutExpired as error:
            logging.warning(f"Stata execution timed out after {timeout:g} seconds")
            raise self._timeout_error(timeout) from error
        finally:
            self._cleanup_process(proc)

    def _execute_windows(
        self,
        dofile_path: Path,
        log_file: Path,
        is_replace: bool = True,
        timeout: float | None = None,
    ):
        """
        Execute Stata on Windows systems

        Args:
            dofile_path: Path to do file
            log_file: Path to log file
            is_replace: Whether replace the log file if exists.
            timeout: Maximum execution time in seconds. None means no timeout.
        """
        batch_file = self._create_windows_batch_file(
            dofile_path,
            log_file,
            is_replace,
        )
        try:
            # Run Stata on Windows using /e to execute the batch file
            cmd = [self.STATA_CLI, "/e", "do", batch_file.as_posix()]
            result = subprocess.run(
                cmd,
                shell=True,  # Windows Stata requires shell execution for proper path resolution and startup
                capture_output=True,
                text=True,
                cwd=self.cwd,
                timeout=timeout,
            )
            if result.returncode != 0:
                logging.error(f"Stata execution failed on Windows: {result.stderr}")
                raise RuntimeError(f"Windows Stata execution failed: {result.stderr}")
            else:
                logging.info(f"Stata execution completed successfully on Windows. Log file: {log_file}")

        except subprocess.TimeoutExpired as error:
            logging.warning(f"Stata execution timed out after {timeout:g} seconds")
            raise self._timeout_error(timeout) from error
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

            batch_log_file = self.cwd / batch_file.with_suffix(".log").name
            try:
                batch_log_file.unlink(missing_ok=True)
            except OSError as error:
                logging.warning(
                    "Failed to remove temporary batch log %s: %s",
                    batch_log_file,
                    error,
                )

    def _execute_unix_like_with_monitors(
        self,
        dofile_path: Path,
        log_name: str,
        is_replace: bool = True,
        enable_smcl: bool = True,
        timeout: float | None = None,
    ) -> Dict[str, Path]:
        """
        Execute Stata on macOS/Linux systems with monitoring enabled.

        Args:
            dofile_path: Path to do file
            log_name: name of log file
            is_replace: Whether replace the log file if exists.
            enable_smcl: Whether to generate SMCL format log.
            timeout: Maximum execution time in seconds. None means no timeout.

        Returns:
            Dict[str, Path]: Dictionary of generated log file paths.
                - "text": .log file path (always present)
                - "smcl": .smcl file path (present if enable_smcl is True)

        Raises:
            RuntimeError: Stata execution error
        """
        # Get environment with terminal size settings
        env = self.set_fake_terminal_size_env()

        logging.info("Launching Stata %s in cwd %s", self.STATA_CLI, self.cwd)
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

            _, stderr = proc.communicate(input=commands, timeout=timeout)

            if proc.returncode != 0:
                logging.error(f"Stata execution failed: {stderr}")
                raise RuntimeError(f"Something went wrong: {stderr}")
            else:
                logging.info(f"Stata execution completed successfully. Log file: {log_file}")

            generated_log_paths = {"text": log_file}
            if enable_smcl:
                generated_log_paths["smcl"] = smcl_file
            return generated_log_paths
        except subprocess.TimeoutExpired as error:
            logging.warning(f"Stata execution timed out after {timeout:g} seconds")
            raise self._timeout_error(timeout) from error
        finally:
            # Stop monitors first
            for monitor in self.monitors:
                try:
                    monitor.stop()
                except Exception as e:
                    logging.warning(f"Monitor stop failed: {e}")
            # Then cleanup process
            self._cleanup_process(proc)

    def _execute_windows_with_monitors(
        self,
        dofile_path: Path,
        log_file: Path,
        is_replace: bool = True,
        timeout: float | None = None,
    ):
        """
        Execute Stata on Windows systems with monitoring enabled.

        Args:
            dofile_path: Path to do file
            log_file: Path to log file
            is_replace: Whether replace the log file if exists.
            timeout: Maximum execution time in seconds. None means no timeout.

        Raises:
            RuntimeError: Stata execution error
        """
        batch_file = self._create_windows_batch_file(
            dofile_path,
            log_file,
            is_replace,
        )
        proc: Optional[subprocess.Popen] = None

        try:
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
            _, stderr = proc.communicate(timeout=timeout)

            if proc.returncode != 0:
                logging.error(f"Stata execution failed on Windows: {stderr}")
                raise RuntimeError(f"Windows Stata execution failed: {stderr}")
            else:
                logging.info(f"Stata execution completed successfully on Windows. Log file: {log_file}")

        except subprocess.TimeoutExpired as error:
            logging.warning(f"Stata execution timed out after {timeout:g} seconds")
            raise self._timeout_error(timeout) from error
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

            batch_log_file = self.cwd / batch_file.with_suffix(".log").name
            try:
                batch_log_file.unlink(missing_ok=True)
            except OSError as error:
                logging.warning(
                    "Failed to remove temporary batch log %s: %s",
                    batch_log_file,
                    error,
                )

    @staticmethod
    def read_log(log_file_path, mode="r", encoding="utf-8") -> str:
        try:
            with open(log_file_path, mode, encoding=encoding) as file:
                log_content = file.read()
            return log_content
        except Exception as e:
            logging.error("Failed to read log file %s: %s", log_file_path, e)
            return f"Failed to read logfile-{log_file_path}: {e}"
