# MCP Resources

MCP-for-Stata does not currently register any MCP resources.

Stata command documentation remains available through the `help` MCP tool on
macOS and Linux. Call `help(cmd="regress")`, for example, instead of using a
`help://stata/{cmd}` resource URI.

The resource form was disabled because its URI template was incompatible with
the current FastMCP parameter handling. Until resource registration is restored
in the server implementation, clients should not advertise or request the
former `help://stata/{cmd}` resource.

See [MCP Tools](tools.md#help) for the supported interface.
