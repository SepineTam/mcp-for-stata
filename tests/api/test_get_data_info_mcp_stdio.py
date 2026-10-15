"""End-to-end stdio protocol regression tests for get_data_info."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import anyio
import pytest
from mcp import Client, Implementation, StdioServerParameters


@pytest.mark.parametrize(
    ("mode", "expected_protocol"),
    [
        ("auto", "2026-07-28"),
        ("legacy", "2025-11-25"),
    ],
)
@pytest.mark.parametrize("boolean_data", [False, True])
def test_get_data_info_stdio_schema_and_response_remain_compatible(
    tmp_path: Path,
    mode: str,
    expected_protocol: str,
    boolean_data: bool,
) -> None:
    """Diagnostic logging must not alter schema, structured output, or stdio framing."""
    working_dir = tmp_path / "workspace"
    working_dir.mkdir()
    data_path = working_dir / "sample.csv"
    data_path.write_text(
        "x,flag\n1,True\n3,False\n" if boolean_data else "x,y\n1,2\n3,4\n",
        encoding="utf-8",
    )
    source_bytes = data_path.read_bytes()
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[DEBUG.logging]",
                "LOGGING_ON = false",
                "",
                "[BETA]",
                "enable_windows_data_info = true",
                "",
                "[PROJECT]",
                f'WORKING_DIR = "{working_dir.as_posix()}"',
                "",
                "[data_info]",
                "is_cache = false",
                'metrics = ["q1", "q3"]',
            ]
        ),
        encoding="utf-8",
    )

    async def _run_protocol_test() -> None:
        server = StdioServerParameters(
            command=sys.executable,
            args=[
                "-c",
                "from stata_mcp.cli import main; main()",
                "-c",
                str(config_path),
            ],
            cwd=str(working_dir),
            env={"PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src")},
        )
        client_name = f"audit-test-{mode}"
        async with Client(
            server,
            mode=mode,
            client_info=Implementation(name=client_name, version="1.0.0"),
        ) as client:
            protocol_version = client.protocol_version
            listed_tools = await client.list_tools()
            tool = next(item for item in listed_tools.tools if item.name == "get_data_info")
            result = await client.call_tool(
                "get_data_info",
                {"data_path": str(data_path), "head": 2 if boolean_data else 0},
            )

        assert protocol_version == expected_protocol
        assert set(tool.input_schema["properties"]) == {
            "data_path",
            "vars_list",
            "encoding",
            "head",
        }
        assert tool.output_schema["properties"]["result"]["type"] == "string"
        assert result.is_error is False
        assert result.structured_content is not None
        text_result = result.content[0].text
        assert result.structured_content["result"] == text_result
        assert text_result.startswith("{"), text_result
        data_info = json.loads(text_result)
        assert data_info["overview"]["obs"] == 2
        assert data_path.read_bytes() == source_bytes
        if boolean_data:
            assert data_info["vars_detail"]["flag"]["type"] == "bool"
            assert data_info["vars_detail"]["flag"]["summary"] == {
                "obs": 2,
                "mean": 0.5,
                "stderr": 0.5,
                "min": 0.0,
                "max": 1.0,
                "q1": 0.25,
                "q3": 0.75,
            }
            assert data_info["head"][0]["flag"] is True
            assert data_info["head"][1]["flag"] is False
            assert data_info["vars_detail"]["x"]["type"] == "float"

        audit_path = working_dir / ".statamcp" / "audit" / "get_data_info.jsonl"
        audit_events = [
            json.loads(line)
            for line in audit_path.read_text(encoding="utf-8").splitlines()
        ]
        assert [event["event"] for event in audit_events] == [
            "started",
            "completed",
        ]
        assert {event["run_id"] for event in audit_events} == {
            audit_events[0]["run_id"]
        }
        assert audit_events[0]["client"] == {
            "name": client_name,
            "version": "1.0.0",
        }
        assert audit_events[0]["protocol_version"] == expected_protocol

        checkpoint_events = [
            json.loads(line)
            for line in (
                working_dir / ".statamcp" / "debug" / "checkpoints.jsonl"
            )
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        assert [
            event["event"]
            for event in checkpoint_events
            if event["step"] == "get_data_info.tool_execution"
        ] == ["started", "completed"]
        assert {
            event["run_id"]
            for event in checkpoint_events
            if event["step"] == "get_data_info.tool_execution"
        } == {audit_events[0]["run_id"]}
        dataframe_events = [
            event
            for event in checkpoint_events
            if event["step"] == "get_data_info.dataframe_read"
        ]
        assert [event["event"] for event in dataframe_events] == [
            "started",
            "completed",
        ]
        assert {
            event["attributes"]["occurrence"] for event in dataframe_events
        } == {1}

        trace_events = [
            json.loads(line)
            for line in (
                working_dir / ".statamcp" / "debug" / "traces.jsonl"
            )
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        tool_span = next(
            event
            for event in trace_events
            if event["name"] == "tools/call get_data_info"
        )
        assert tool_span["attributes"]["statamcp.run_id"] == audit_events[0][
            "run_id"
        ]

    anyio.run(_run_protocol_test)
