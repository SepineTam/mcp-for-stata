# Stata Help

> **macOS and Linux Only!**

This module is currently only supported on macOS and Linux systems. Windows support is not available at this time.

## Overview

StataHelp is a utility module that retrieves help documentation for Stata commands directly from your local Stata installation. It provides quick access to Stata's built-in help system with intelligent caching for improved performance.

## Key Features

### Local Help Access

StataHelp queries the Stata help system installed on your machine:

- **No Internet Required**: All help documentation comes from your local Stata installation
- **Fast Access**: Retrieves help information instantly through Stata CLI
- **Complete Documentation**: Access the same comprehensive help available in Stata

### Intelligent Caching System

StataHelp includes a multi-level caching mechanism to improve performance:

- **Project-Level Cache**: Saves help results to your project's temporary directory for quick access
- **Global Cache**: Stores help files in `~/.statamcp/help/` for reuse across projects
- **Environment Control**: Use `STATA_MCP__CACHE_HELP` and `STATA_MCP__SAVE_HELP` to control caching behavior

### Command Validation

Before executing a Stata command, you can use StataHelp to verify if the command exists:

- Checks if help documentation is available for a given command
- Helps prevent errors from typos or missing packages
- Useful for validating user input in automated workflows

## Use Cases

- **Command Verification**: Check if a Stata command exists before execution
- **Documentation Lookup**: Retrieve help text for Stata commands programmatically
- **Interactive Assistance**: Provide in-context help in AI-powered Stata workflows
- **Error Prevention**: Validate commands before running them in scripts

## How It Works

1. **Command Validation**: Normalizes and validates the command name before any cache or Stata access
2. **Cache Check**: Selects the newest non-empty result from the enabled project and global caches
3. **Stata Query**: If not cached, sends `help {command}` request to Stata CLI
4. **Documentation Retrieval**: Stata searches its local documentation for the specified command
5. **Cache Storage**: Saves the result to cache (if enabled)
6. **Result Return**: Returns the help text for display or processing

Use `replace=True` to skip cache lookup, query Stata, and overwrite the project and
global cache files. There is no automatic TTL-based refresh.

## Configuration

Control caching behavior with environment variables:

```bash
# Enable global caching (default: true)
export STATA_MCP__CACHE_HELP=true

# Enable project-level saving (default: true)
export STATA_MCP__SAVE_HELP=true
```

## Limitations

- **Platform Support**: Currently only works on macOS and Linux
- **Local Documentation Only**: Cannot access help for packages that are not installed locally
- **No Internet Search**: Does not perform online searches for missing commands

## File Locations

- **Global Cache Directory**: `~/.statamcp/help/`
- **Project Cache Directory**: `{project_tmp_dir}/` (usually in `stata-mcp-tmp/`)
