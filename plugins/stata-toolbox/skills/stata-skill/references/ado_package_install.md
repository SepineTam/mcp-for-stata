# `ado_package_install`

Install a Stata ado package from SSC, GitHub, or net sources.

## Parameters

| Parameter | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `package` | `str` | Yes | — | Package name. For GitHub, use "user/repo" format |
| `source` | `"ssc" \| "github" \| "net"` | No | `"ssc"` | Package source |
| `is_replace` | `bool` | No | `false` | Force reinstallation if already present |
| `package_source_from` | `str \| None` | No | `None` | Allowlisted HTTPS URL required for `source="net"` |

## Input Validation

- The operator must enable installation and start the MCP server with the unsafe profile
- SSC packages and GitHub repositories require exact allowlist entries
- Net sources require an allowlisted HTTPS hostname and exact source URL
- `source` must be exactly `ssc`, `github`, or `net`; unknown values are rejected
- Local paths, IP hosts, credentials, queries, fragments, and non-default ports are rejected
- Every MCP call elicits approval from the user through the client and fails closed without it
- Validation occurs again immediately before the installer sends a command to Stata

## Operator Setup

Configure exact allowlists in `~/.statamcp/config.toml`, then start the MCP
server with `stata-mcp server --unsafe`. The plugin's default MCP configuration
does not expose this high-risk tool.

```toml
[SECURITY]
ENABLE_ADO_INSTALL = true
ADO_INSTALL_ALLOWED_SSC_PACKAGES = ["reghdfe"]
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = ["SepineTam/TexIV"]
ADO_INSTALL_ALLOWED_NET_HOSTS = ["packages.example.com"]
ADO_INSTALL_ALLOWED_NET_SOURCES = ["https://packages.example.com/stata"]
```

## Returns

String containing the Stata installation log.

## Sources

### SSC (Statistical Software Components)

The default and most common source. Hosted by Boston College.

```python
ado_package_install("outreg2")
ado_package_install("reghdfe")
ado_package_install("estout", is_replace=false)
```

**Note:** SSC installations can be slow due to network latency. If the package is likely already installed, consider asking the user before installing.

### GitHub

For packages distributed via GitHub repositories.

```python
ado_package_install("SepineTam/TexIV", source="github")
```

**Note:** The package repository must follow Stata package conventions with a valid `.pkg` file.

### Net

For packages hosted on explicitly allowlisted HTTPS web servers. Local
directories are rejected.

```python
ado_package_install("mypackage", source="net", package_source_from="https://example.com/stata")
```

## When to Use

- Before running commands that require third-party packages
- When the user mentions a command does not exist or is not recognized
- When setting up a new analysis environment

## Platform Differences

| Platform | SSC | GitHub | Net |
|:---|:---|:---|:---|
| macOS | Native CLI | Native CLI | Native CLI |
| Linux | Native CLI | Native CLI | Native CLI |
| Windows | Do-file delegation | Do-file delegation | Do-file delegation |

On Windows, package installation is handled by writing and executing a temporary do-file, which may be slower than native CLI installation on Unix.

## Post-Installation

The tool does not implicitly install the GitHub helper or refresh the help cache.
Review the installation result, then call `help(cmd="package_name", replace=true)`
explicitly if refreshed help is needed.

## Example

```python
# Install outreg2 from SSC
ado_package_install("outreg2")

# Install from GitHub without overwriting
ado_package_install("user/repo", source="github", is_replace=false)

# Install from a custom URL
ado_package_install("custompkg", source="net", package_source_from="https://site.example/stata")
```

## Common Packages

| Package | Source | Purpose |
|:---|:---|:---|
| `outreg2` | SSC | Regression output tables |
| `reghdfe` | SSC | High-dimensional fixed effects regression |
| `estout` | SSC | Export estimation results |
| `ftools` | SSC | Faster Stata tools (dependency for reghdfe) |
| `ivreg2` | SSC | Extended instrumental variables regression |
