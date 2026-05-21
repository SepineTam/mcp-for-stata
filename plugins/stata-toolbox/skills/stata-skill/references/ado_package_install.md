# `ado_package_install`

Install a Stata ado package from SSC, GitHub, or net sources.

## Parameters

| Parameter | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `package` | `str` | Yes | — | Package name. For GitHub, use "user/repo" format |
| `source` | `"ssc" \| "github" \| "net"` | No | `"ssc"` | Package source |
| `is_replace` | `bool` | No | `true` | Force reinstallation if already present |
| `package_source_from` | `str \| None` | No | `None` | Directory or URL (required only for `source="net"`) |

## Returns

String containing the Stata installation log.

## Sources

### SSC (Statistical Software Components)

The default and most common source. Hosted by Boston College.

```python
ado_package_install("outreg2")
ado_package_install("reghdfe")
ado_package_install("estout", is_replace=false)  # skip if exists
```

**Note:** SSC installations can be slow due to network latency. If the package is likely already installed, consider asking the user before installing.

### GitHub

For packages distributed via GitHub repositories.

```python
ado_package_install("SepineTam/TexIV", source="github")
ado_package_install("someuser/stata-pkg", source="github", is_replace=false)
```

**Note:** The package repository must follow Stata package conventions with a valid `.pkg` file.

### Net

For packages hosted on custom web servers or local directories.

```python
ado_package_install("mypackage", source="net", package_source_from="https://example.com/stata/")
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

After successful installation, the tool attempts to refresh the help cache for the installed package. This means `help("package_name")` should work immediately on Unix systems.

## Example

```python
# Install outreg2 from SSC
ado_package_install("outreg2")

# Install from GitHub without overwriting
ado_package_install("user/repo", source="github", is_replace=false)

# Install from a custom URL
ado_package_install("custompkg", source="net", package_source_from="http://site.com/stata/")
```

## Common Packages

| Package | Source | Purpose |
|:---|:---|:---|
| `outreg2` | SSC | Regression output tables |
| `reghdfe` | SSC | High-dimensional fixed effects regression |
| `estout` | SSC | Export estimation results |
| `ftools` | SSC | Faster Stata tools (dependency for reghdfe) |
| `ivreg2` | SSC | Extended instrumental variables regression |
