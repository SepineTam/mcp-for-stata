"""Tests that the Windows launcher batch filename is never derived from user input.

The batch path is passed to a shell on Windows, so the do-file name (whose
stem may legally contain characters that cmd.exe treats as syntax) must never
be interpolated into the batch filename. Regression guard for the fix that
replaced ``{dofile_path.stem}`` with a random uuid-based name in both
``_execute_windows`` and ``_execute_windows_with_monitors``.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from stata_mcp.stata.stata_do.do import StataDo

BATCH_NAME_PATTERN = re.compile(
    r"^stata_batch__[0-9a-f]{32}__[A-Za-z0-9_]+\.do$"
)
UUID_BATCH_NAME_PATTERN = re.compile(r"^stata_batch__[0-9a-f]{32}\.do$")
METACHARACTERS = "&^%!"


class TestGenerateBatchFileName:
    def test_matches_safe_pattern(self):
        name = StataDo._generate_batch_file_name()

        assert UUID_BATCH_NAME_PATTERN.fullmatch(name)

    def test_unique_across_calls(self):
        names = {StataDo._generate_batch_file_name() for _ in range(64)}

        assert len(names) == 64

    def test_contains_no_shell_metacharacters(self):
        for _ in range(16):
            name = StataDo._generate_batch_file_name()

            assert not any(char in name for char in METACHARACTERS)


class TestCreateWindowsBatchFile:
    def test_creates_complete_wrapper_with_safe_name(self, executor, malicious_dofile):
        log_file = executor.log_file_path / "run.log"

        batch_file = executor._create_windows_batch_file(
            malicious_dofile.resolve(),
            log_file,
            True,
        )

        try:
            assert BATCH_NAME_PATTERN.fullmatch(batch_file.name)
            wrapper = batch_file.read_text(encoding="utf-8")
            assert f'log using "{log_file}", replace' in wrapper
            assert f'do "{malicious_dofile.resolve()}"' in wrapper
        finally:
            batch_file.unlink(missing_ok=True)


class _FakeCompletedProcess:
    returncode = 0
    stdout = ""
    stderr = ""


class _FakePopen:
    returncode = 0

    def poll(self):
        return 0

    def communicate(self, timeout=None):
        return ("", "")

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 0

    def kill(self):
        pass


@pytest.fixture
def malicious_dofile(tmp_path: Path) -> Path:
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    dofile = work_dir / "x&calc.exe&.do"
    dofile.write_text("display 123\n")
    return dofile


@pytest.fixture
def executor(tmp_path: Path) -> StataDo:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return StataDo(
        stata_cli=r"C:\Program Files\Stata18\StataMP-64.exe",
        log_file_path=log_dir,
        is_unix=False,
        cwd=tmp_path,
    )


class TestExecuteWindowsUsesSafeBatchName:
    def test_run_command_line_has_no_metacharacters(
        self, monkeypatch, executor, malicious_dofile, tmp_path
    ):
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = list(cmd)
            captured["kwargs"] = kwargs
            return _FakeCompletedProcess()

        monkeypatch.setattr(
            "stata_mcp.stata.stata_do.do.subprocess.run", fake_run
        )

        executor.execute_dofile(malicious_dofile)

        cmd = captured["cmd"]
        assert BATCH_NAME_PATTERN.fullmatch(Path(cmd[3]).name)
        assert not any(char in " ".join(cmd) for char in "&^%!")
        assert "calc.exe" not in " ".join(cmd)
        assert captured["kwargs"]["shell"] is True
        assert not Path(cmd[3]).exists()


class TestExecuteWindowsWithMonitorsUsesSafeBatchName:
    def test_popen_command_line_has_no_metacharacters(
        self, monkeypatch, executor, malicious_dofile
    ):
        captured = {}

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = list(cmd)
            captured["kwargs"] = kwargs
            return _FakePopen()

        monkeypatch.setattr(
            "stata_mcp.stata.stata_do.do.subprocess.Popen", fake_popen
        )
        executor.monitors = [SimpleNamespace(start=lambda proc: None,
                                             stop=lambda: None)]
        executor.IS_MONITOR = True

        executor.execute_dofile(malicious_dofile)

        cmd = captured["cmd"]
        assert BATCH_NAME_PATTERN.fullmatch(Path(cmd[3]).name)
        assert not any(char in " ".join(cmd) for char in "&^%!")
        assert "calc.exe" not in " ".join(cmd)
        assert captured["kwargs"]["shell"] is True
        assert not Path(cmd[3]).exists()


class TestWindowsBatchCleanup:
    def test_removes_batch_file_when_process_launch_fails(
        self, monkeypatch, executor, malicious_dofile
    ):
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["batch_file"] = Path(cmd[3])
            raise OSError("launch failed")

        monkeypatch.setattr(
            "stata_mcp.stata.stata_do.do.subprocess.run", fake_run
        )

        with pytest.raises(OSError, match="launch failed"):
            executor.execute_dofile(malicious_dofile)

        assert not captured["batch_file"].exists()

    def test_removes_monitored_batch_file_after_timeout(
        self, monkeypatch, executor, malicious_dofile
    ):
        captured = {}
        process = Mock()
        process.communicate.side_effect = subprocess.TimeoutExpired("stata", 1)
        process.poll.side_effect = [None, 0]
        process.wait.return_value = 0

        def fake_popen(cmd, **kwargs):
            captured["batch_file"] = Path(cmd[3])
            return process

        monkeypatch.setattr(
            "stata_mcp.stata.stata_do.do.subprocess.Popen", fake_popen
        )
        executor.monitors = [SimpleNamespace(start=lambda proc: None, stop=lambda: None)]
        executor.IS_MONITOR = True

        with pytest.raises(RuntimeError, match="timed out after 1 second"):
            executor.execute_dofile(malicious_dofile, timeout=1)

        assert not captured["batch_file"].exists()
        process.terminate.assert_called_once_with()


@pytest.mark.parametrize("monitored", [False, True])
@pytest.mark.parametrize(
    "outcome", ["success", "execution_error", "timeout", "launch_error", "no_log"]
)
def test_cleans_only_current_batch_log(
    monkeypatch, executor, malicious_dofile, monitored, outcome
):
    captured = {}
    managed_log = executor.log_file_path / "run.log"
    managed_log.write_text("managed output")
    unrelated_log = executor.cwd / "stata_batch__other_run.log"
    unrelated_log.write_text("other run")

    def fake_launch(cmd, **kwargs):
        batch_file = Path(cmd[3])
        batch_log = kwargs["cwd"] / batch_file.with_suffix(".log").name
        captured.update(batch_file=batch_file, batch_log=batch_log)
        assert batch_log.parent != batch_file.parent
        if outcome == "launch_error":
            raise OSError("launch failed")
        if outcome != "no_log":
            batch_log.write_text("automatic batch output")
        if not monitored:
            if outcome == "timeout":
                raise subprocess.TimeoutExpired(cmd, 1)
            return SimpleNamespace(
                returncode=1 if outcome == "execution_error" else 0,
                stderr="execution failed",
            )
        process = Mock()
        process.returncode = 1 if outcome == "execution_error" else 0
        process.poll.return_value = 0
        process.communicate.return_value = ("", "execution failed")
        if outcome == "timeout":
            process.communicate.side_effect = subprocess.TimeoutExpired(cmd, 1)
        return process

    launcher = "Popen" if monitored else "run"
    monkeypatch.setattr(
        f"stata_mcp.stata.stata_do.do.subprocess.{launcher}", fake_launch
    )
    execute = (
        executor._execute_windows_with_monitors
        if monitored else executor._execute_windows
    )
    if outcome == "launch_error":
        expected_error = RuntimeError if monitored else OSError
        with pytest.raises(expected_error, match="launch failed"):
            execute(malicious_dofile, managed_log, timeout=1)
    elif outcome in {"execution_error", "timeout"}:
        message = "execution failed" if outcome == "execution_error" else "timed out"
        with pytest.raises(RuntimeError, match=message):
            execute(malicious_dofile, managed_log, timeout=1)
    else:
        execute(malicious_dofile, managed_log, timeout=1)

    assert not captured["batch_file"].exists()
    assert not captured["batch_log"].exists()
    assert managed_log.read_text() == "managed output"
    assert unrelated_log.read_text() == "other run"


@pytest.mark.parametrize("monitored", [False, True])
@pytest.mark.parametrize("execution_error", [False, True])
def test_batch_log_cleanup_failure_preserves_execution_result(
    monkeypatch, executor, malicious_dofile, caplog, monitored, execution_error
):
    captured = {}
    original_unlink = Path.unlink

    def fake_launch(cmd, **kwargs):
        batch_file = Path(cmd[3])
        batch_log = kwargs["cwd"] / batch_file.with_suffix(".log").name
        batch_log.write_text("automatic batch output")
        captured.update(batch_file=batch_file, batch_log=batch_log)
        if monitored:
            process = Mock()
            process.returncode = 1 if execution_error else 0
            process.poll.return_value = 0
            process.communicate.return_value = ("", "original execution error")
            return process
        return SimpleNamespace(
            returncode=1 if execution_error else 0,
            stderr="original execution error",
        )

    def fail_batch_log_unlink(file_path, *args, **kwargs):
        if file_path == captured.get("batch_log"):
            raise PermissionError("batch log is locked")
        return original_unlink(file_path, *args, **kwargs)

    launcher = "Popen" if monitored else "run"
    monkeypatch.setattr(
        f"stata_mcp.stata.stata_do.do.subprocess.{launcher}", fake_launch
    )
    monkeypatch.setattr(Path, "unlink", fail_batch_log_unlink)
    execute = (
        executor._execute_windows_with_monitors
        if monitored else executor._execute_windows
    )
    managed_log = executor.log_file_path / "run.log"
    if execution_error:
        with pytest.raises(RuntimeError, match="original execution error"):
            execute(malicious_dofile, managed_log)
    else:
        execute(malicious_dofile, managed_log)

    assert not captured["batch_file"].exists()
    assert captured["batch_log"].exists()
    assert "Failed to remove temporary batch log" in caplog.text
    assert "batch log is locked" in caplog.text
