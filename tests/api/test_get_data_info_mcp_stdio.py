"""End-to-end stdio protocol regression tests for get_data_info."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_get_data_info_stdio_schema_and_response_remain_compatible(tmp_path: Path) -> None:
    """Diagnostic logging must not alter schema, structured output, or stdio framing."""
    working_dir = tmp_path / "workspace"
    working_dir.mkdir()
    data_path = working_dir / "sample.csv"
    data_path.write_text("x,y\n1,2\n3,4\n", encoding="utf-8")
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[DEBUG.logging]",
                "LOGGING_ON = false",
                "",
                "[PROJECT]",
                f'WORKING_DIR = "{working_dir.as_posix()}"',
                "",
                "[data_info]",
                "is_cache = false",
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
        )
        async with stdio_client(server) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                listed_tools = await session.list_tools()
                tool = next(item for item in listed_tools.tools if item.name == "get_data_info")
                result = await session.call_tool(
                    "get_data_info",
                    {"data_path": str(data_path)},
                )

        assert set(tool.inputSchema["properties"]) == {
            "data_path",
            "vars_list",
            "encoding",
            "head",
        }
        assert tool.outputSchema["properties"]["result"]["type"] == "string"
        assert result.isError is False
        assert result.structuredContent is not None
        text_result = result.content[0].text
        assert result.structuredContent["result"] == text_result
        assert json.loads(text_result)["overview"]["obs"] == 2

    anyio.run(_run_protocol_test)
