import warnings
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("stata-mcp")
except PackageNotFoundError:
    __version__ = "0.0.0"
    warnings.warn(
        "Package metadata for 'stata-mcp' is unavailable. Falling back to version '0.0.0'.",
        RuntimeWarning,
        stacklevel=1,
    )
__author__ = "Song Tan <sepine@statamcp.com>"

_default_server_cache = None


def _get_default_server():
    """Return the default MCP server with the all-tools profile registered."""
    global _default_server_cache

    if _default_server_cache is not None:
        return _default_server_cache

    try:
        from .mcp_servers import register_tools
        from .mcp_servers import stata_mcp as server

        register_tools(server, profile="all")
    except AttributeError as error:
        raise RuntimeError(
            "Failed to initialize the default 'stata_mcp' server due to an internal attribute error."
        ) from error

    _default_server_cache = server
    return _default_server_cache


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
