# Stata Package Installation

## Overview

The package installation module is a high-risk interface for installing
approved Stata packages. The MCP tool is disabled by default and requires
client-mediated approval. CLI calls prompt unless `-y` or `--yes` is supplied.
The Python API does not require caller confirmation. All interfaces validate
command arguments, and GitHub repositories require an exact repository
allowlist.

## Key Features

### SSC Archive Integration

Directly installs packages from the Boston College Statistical Software Components archive:

- **Controlled Installation**: SSC package names may contain only ASCII letters and numbers
- **Dependency Handling**: Stata's package manager handles dependencies automatically
- **Version Management**: Supports updating existing packages with the `replace` option

### Cross-Platform Support

Works on all supported operating systems:

- **Windows**: Full support through Stata's batch execution mode
- **macOS**: Native support through Stata CLI
- **Linux**: Native support through Stata CLI

### Installation Verification

The module provides built-in verification to ensure successful installation:

- Checks for installation success messages
- Handles already-installed packages gracefully
- Returns clear status messages for troubleshooting

## Use Cases

- **Automated Setup**: Install required packages in automated research workflows
- **Environment Initialization**: Prepare Stata environments with necessary packages
- **Missing Package Recovery**: Install only after the exact package and source are approved
- **CI/CD Pipelines**: Set up consistent Stata environments in automated testing

## How It Works

1. **Authorization**: Requires enablement and approval; GitHub also requires an exact repository allowlist
2. **Validation**: Revalidates the package and source immediately before execution
3. **Stata Execution**: Sends the validated installation command to Stata
4. **Result Verification**: Checks explicit success indicators

## Installation Behavior

By default, the installer does not use the `replace` option:

- **New Packages**: Installs the package for the first time
- **Existing Packages**: Replaces with the latest version from SSC
- **Up-to-Date Packages**: Skips installation if already at the latest version

## Common Packages

Some frequently installed packages include:

- **`estout`**: Regression and estimation tables
- **`outreg2`**: Alternative regression table output
- **`coefplot`**: Coefficient plots
- **`tabout`**: Export tables to various formats
- **`graphexport`**: Enhanced graph export options

## Error Handling

The module handles common installation scenarios:

- Package not found on SSC
- Network connectivity issues
- File permission problems
- Stata license limitations

## Example Workflow

```python
# Python API example after enabling installation
ado_package_install("estout")
```

## Notes

- Requires internet connection for SSC access
- Installation speed depends on package size and network connection
- Some packages may have additional system requirements
- Always verify package functionality after installation
- Successful installs attempt to refresh help with `replace=True` for the likely command name
- GitHub repository contents receive no security protection; inspect them before installation
- Direct package-management commands submitted through `stata_do` are blocked; use the controlled interface
