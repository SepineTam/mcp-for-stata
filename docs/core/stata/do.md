# Stata Do File Executor

## Overview

StataDo is the core module in Stata-MCP responsible for executing Stata do files. It provides a secure and reliable way to run Stata scripts with automatic result logging, supporting three major operating systems: macOS, Linux, and Windows.

## Key Features

### Cross-Platform Support

StataDo automatically adapts to different operating systems:

- **Unix-like Systems (macOS/Linux)**: Interacts with Stata through standard input stream for efficient command execution
- **Windows Systems**: Uses batch file method to execute Stata commands, ensuring compatibility

### Automatic Logging

Every time a do file is executed, StataDo automatically:

1. Creates a new log file or creates a log at the specified path
2. Records the complete Stata execution process and output results
3. Saves log files in the `stata-mcp-log` directory for easy review and analysis

### Security Guarantees

StataDo includes built-in security check mechanisms:

- **Command Filtering**: Blocks shell-escape commands that may compromise system security (such as `!cmd` or `shell cmd`)
- **Content Validation**: Checks do file content before execution to prevent malicious command execution

### Smart Terminal Emulation

StataDo simulates a standard terminal environment to ensure consistent and readable Stata output:

- Sets fixed terminal dimensions (120 columns × 40 lines)
- Ensures cross-platform output consistency

## Workflow

1. **Preparation Phase**: Accepts do file path and log file path parameters
2. **Security Check**: Validates do file content to ensure no dangerous commands
3. **Environment Adaptation**: Selects appropriate execution method based on operating system type
4. **Script Execution**: Calls Stata CLI to execute the do file
5. **Result Logging**: Writes execution process and results to log file
6. **Cleanup**: Removes temporary files (Windows platform)

## Use Cases

StataDo is primarily used in the following scenarios:

- **Batch Data Processing**: Executes do files containing data cleaning, transformation, and other operations
- **Statistical Analysis**: Runs regression analysis, descriptive statistics, and other Stata commands
- **Chart Generation**: Executes Stata scripts that generate statistical charts
- **Automated Research Workflows**: Calls Stata for data analysis in AI Agents or automated scripts

## Integration with Other Modules

StataDo is an important part of the Stata-MCP toolchain:

- **StataFinder**: Provides the path to the Stata executable
- **StataController**: Provides higher-level Stata control interfaces
- **Logging System**: Automatically records execution results in the specified log directory

## File Path Conventions

StataDo follows the Stata-MCP directory structure conventions:

- **Do File Directory**: `~/Documents/.statamcp/stata-mcp-dofile/`
- **Log File Directory**: `~/Documents/.statamcp/stata-mcp-log/`

## Important Notes

1. **File Encoding**: StataDo reads do files using UTF-8 encoding; ensure your do files are saved with UTF-8 encoding
2. **Path Handling**: On Windows systems, spaces in paths are automatically handled
3. **Log Overwriting**: By default, existing log files will be overwritten; this behavior can be controlled via parameters
4. **Error Handling**: Exceptions are thrown when execution fails; callers should properly handle these exceptions