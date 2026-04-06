from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("stata-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"
__author__ = "Song Tan <sepine@statamcp.com>"


def _get_default_server():
    """Return the default MCP server with the all-tools profile registered."""
    from .mcp_servers import register_tools, stata_mcp as server

    register_tools(server, profile="all")
    return server


def __getattr__(name: str):
    """Provide lazy access to exported package attributes."""
    if name == "stata_mcp":
        return _get_default_server()
    if name == "main":
        from .cli import main as cli_main

        return cli_main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "main",
    "stata_mcp",
]


if __name__ == "__main__":
    print(f"Hello Stata-MCP@v{__version__}")
    __getattr__("main")()
