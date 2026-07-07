"""Tests for asynchronous Stata do-file execution."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import Mock

import pytest

from stata_mcp.stata.stata_do.async_do import AsyncStataDo


def _dofile(tmp_path: Path, name: str = "analysis.do") -> Path:
    dofile = tmp_path / name
    dofile.write_text("display 1", encoding="utf-8")
    return dofile


class _FakeAsyncProcess:
    def __init__(
        self,
        tracker: dict[str, int | list[bytes]],
        returncode: int = 0,
        stderr: bytes = b"",
        wait_blocks: bool = False,
    ):
        self.returncode = None
        self._tracker = tracker
        self._final_returncode = returncode
        self._stderr = stderr
        self._wait_blocks = wait_blocks
        self.terminated = False
        self.killed = False

    async def communicate(self, input: bytes | None = None):
        self._tracker["commands"].append(input or b"")
        self._tracker["active"] += 1
        self._tracker["max_active"] = max(
            self._tracker["max_active"],
            self._tracker["active"],
        )
        await asyncio.sleep(0.01)
        self._tracker["active"] -= 1
        self.returncode = self._final_returncode
        return b"", self._stderr

    def terminate(self) -> None:
        self.terminated = True
        if not self._wait_blocks:
            self.returncode = -15

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    async def wait(self):
        if self._wait_blocks:
            await asyncio.sleep(10)
        return self.returncode


def _tracker() -> dict[str, int | list[bytes]]:
    return {"active": 0, "max_active": 0, "commands": []}


def test_execute_dofiles_runs_with_concurrency_limit_and_preserves_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    tracker = _tracker()

    async def fake_create_subprocess_exec(*args, **kwargs):
        return _FakeAsyncProcess(tracker)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    executor = AsyncStataDo("stata", tmp_path, is_unix=True)
    dofiles = [_dofile(tmp_path, f"job_{index}.do") for index in range(3)]

    result = asyncio.run(
        executor.execute_dofiles(
            dofiles,
            log_file_names=["first", "second", "third"],
            max_concurrency=2,
        )
    )

    assert [item["text"].name for item in result] == [
        "first.log",
        "second.log",
        "third.log",
    ]
    assert [item["smcl"].name for item in result] == [
        "first.smcl",
        "second.smcl",
        "third.smcl",
    ]
    assert tracker["max_active"] == 2
    assert len(tracker["commands"]) == 3


def test_execute_dofile_async_generates_text_only_when_smcl_disabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    tracker = _tracker()

    async def fake_create_subprocess_exec(*args, **kwargs):
        return _FakeAsyncProcess(tracker)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    executor = AsyncStataDo("stata", tmp_path, is_unix=True)

    result = asyncio.run(
        executor.execute_dofile_async(
            _dofile(tmp_path),
            log_file_name="run",
            enable_smcl=False,
        )
    )

    assert result == {"text": tmp_path / "run.log"}
    command_text = tracker["commands"][0].decode("utf-8")
    assert "run.log" in command_text
    assert "run.smcl" not in command_text


def test_execute_dofile_async_raises_when_stata_process_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    tracker = _tracker()

    async def fake_create_subprocess_exec(*args, **kwargs):
        return _FakeAsyncProcess(tracker, returncode=1, stderr=b"boom")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    executor = AsyncStataDo("stata", tmp_path, is_unix=True)

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(
            executor.execute_dofile_async(
                _dofile(tmp_path),
                log_file_name="run",
            )
        )


def test_execute_dofile_async_cleans_up_after_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    tracker = _tracker()
    process = _FakeAsyncProcess(tracker, wait_blocks=False)

    async def slow_communicate(input: bytes | None = None):
        await asyncio.sleep(10)
        return b"", b""

    process.communicate = slow_communicate

    async def fake_create_subprocess_exec(*args, **kwargs):
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    executor = AsyncStataDo("stata", tmp_path, is_unix=True)

    with pytest.raises(RuntimeError, match="timed out after 0.01 seconds"):
        asyncio.run(
            executor.execute_dofile_async(
                _dofile(tmp_path),
                log_file_name="run",
                timeout=0.01,
            )
        )

    assert process.terminated is True
    assert process.killed is False


def test_execute_dofiles_rejects_invalid_parallel_arguments(tmp_path: Path) -> None:
    executor = AsyncStataDo("stata", tmp_path, is_unix=True)
    dofiles = [_dofile(tmp_path, "one.do"), _dofile(tmp_path, "two.do")]

    with pytest.raises(ValueError, match="must match"):
        asyncio.run(executor.execute_dofiles(dofiles, log_file_names=["only-one"]))

    with pytest.raises(ValueError, match="unique"):
        asyncio.run(executor.execute_dofiles(dofiles, log_file_names=["same", "same"]))

    with pytest.raises(ValueError, match="positive integer"):
        asyncio.run(executor.execute_dofiles(dofiles, max_concurrency=0))


def test_execute_dofiles_rejects_parallel_shared_monitors(tmp_path: Path) -> None:
    executor = AsyncStataDo("stata", tmp_path, is_unix=True, monitors=[Mock()])
    dofiles = [_dofile(tmp_path, "one.do"), _dofile(tmp_path, "two.do")]

    with pytest.raises(RuntimeError, match="shared monitors"):
        asyncio.run(executor.execute_dofiles(dofiles, max_concurrency=2))


def test_execute_dofile_async_uses_sync_fallback_for_windows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    executor = AsyncStataDo("stata", tmp_path, is_unix=False)
    expected = {"text": tmp_path / "fallback.log"}
    execute_dofile = Mock(return_value=expected)
    monkeypatch.setattr(executor, "execute_dofile", execute_dofile)

    result = asyncio.run(
        executor.execute_dofile_async(
            _dofile(tmp_path),
            log_file_name="fallback",
            timeout=3,
        )
    )

    assert result == expected
    execute_dofile.assert_called_once_with(
        tmp_path / "analysis.do",
        "fallback",
        True,
        True,
        3,
    )
