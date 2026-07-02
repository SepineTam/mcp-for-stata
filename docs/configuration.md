# Configuration System

MCP-for-Stata uses a hierarchical configuration system with three levels of priority:

1. **Environment Variables** (highest priority)
2. **Configuration File** (`~/.statamcp/config.toml`)
3. **Default Values** (lowest priority)

## Configuration File

### Location

The configuration file is located at:
```
~/.statamcp/config.toml
```

On different platforms:
- **macOS/Linux**: `/home/username/.statamcp/config.toml`
- **Windows**: `C:\Users\Username\.statamcp\config.toml`

### Example Configuration

```toml
[DEBUG]
IS_DEBUG = false

[DEBUG.logging]
LOGGING_ON = true
LOGGING_CONSOLE_HANDLER_ON = false
LOGGING_FILE_HANDLER_ON = true
LOG_FILE = "~/.statamcp/stata_mcp_debug.log"
MAX_BYTES = 10_000_000
BACKUP_COUNT = 5

[BETA]
ENABLE_WRITE_DOFILE = false

[HELP]
IS_CACHE = true
IS_SAVE = true

[SECURITY]
IS_GUARD = true
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = []

[PROJECT]
WORKING_DIR = ""
CLEAN_LOG_DAYS = -1
FOLDER_TAG = ".statamcp"

[MONITOR]
IS_MONITOR = false
MAX_RAM_MB = -1

[STATA]
# Optional: Override automatic Stata detection
# STATA_CLI = "/path/to/stata-mp"

[data_info]
metrics = ["obs", "mean", "stderr", "min", "max", "q1", "q3", "skewness", "kurtosis"]
string_keep_number = 10
decimal_places = 3
hash_length = 12
```

## Configuration Sections

### DEBUG Section

Controls debugging and logging behavior.

#### `DEBUG.IS_DEBUG`

Enable debug mode for verbose output.

- **Type**: Boolean
- **Default**: `false`
- **Environment Variable**: `STATA_MCP__IS_DEBUG`
- **Example**:
  ```bash
  export STATA_MCP__IS_DEBUG=true
  ```

#### `DEBUG.logging.LOGGING_ON`

Enable or disable all logging.

- **Type**: Boolean
- **Default**: `true`
- **Environment Variable**: `STATA_MCP__LOGGING_ON`
- **Example**:
  ```bash
  export STATA_MCP__LOGGING_ON=false
  ```

#### `DEBUG.logging.LOGGING_CONSOLE_HANDLER_ON`

Enable console output for logs.

- **Type**: Boolean
- **Default**: `false`
- **Environment Variable**: `STATA_MCP__LOGGING_CONSOLE_HANDLER_ON`
- **Example**:
  ```bash
  export STATA_MCP__LOGGING_CONSOLE_HANDLER_ON=true
  ```

#### `DEBUG.logging.LOGGING_FILE_HANDLER_ON`

Enable file logging.

- **Type**: Boolean
- **Default**: `true`
- **Environment Variable**: `STATA_MCP__LOGGING_FILE_HANDLER_ON`
- **Example**:
  ```bash
  export STATA_MCP__LOGGING_FILE_HANDLER_ON=true
  ```

#### `DEBUG.logging.LOG_FILE`

Specify the log file location.

- **Type**: Path (string)
- **Default**: `~/.statamcp/stata_mcp_debug.log`
- **Environment Variable**: `STATA_MCP__LOG_FILE`
- **Example**:
  ```bash
  export STATA_MCP__LOG_FILE="/var/log/stata-mcp/debug.log"
  ```

#### `DEBUG.logging.MAX_BYTES`

Maximum size of a single log file before rotation.

- **Type**: Integer (bytes)
- **Default**: `10_000_000` (10 MB)
- **Environment Variable**: `STATA_MCP__LOGGING__MAX_BYTES`
- **Example**:
  ```bash
  export STATA_MCP__LOGGING__MAX_BYTES=50_000_000
  ```

#### `DEBUG.logging.BACKUP_COUNT`

Number of backup log files to keep.

- **Type**: Integer
- **Default**: `5`
- **Environment Variable**: `STATA_MCP__LOGGING__BACKUP_COUNT`
- **Example**:
  ```bash
  export STATA_MCP__LOGGING__BACKUP_COUNT=10
  ```

### HELP Section

Controls caching behavior for the `help` tool.

#### `HELP.IS_CACHE`

Enable in-memory caching of help results returned by the `help` tool.

- **Type**: Boolean
- **Default**: `true`
- **Environment Variable**: `STATA_MCP__CACHE_HELP`
- **Description**: When enabled, previously fetched help text for the same command is served from cache, reducing repeated Stata calls within a session.
- **Example**:
  ```bash
  export STATA_MCP__CACHE_HELP=true
  ```

#### `HELP.IS_SAVE`

Persist cached help results to disk under `~/.statamcp/help/`.

- **Type**: Boolean
- **Default**: `true`
- **Environment Variable**: `STATA_MCP__SAVE_HELP`
- **Description**: When enabled, help responses are saved as files and reused across sessions. Disable this if you prefer a strictly in-memory cache.
- **Example**:
  ```bash
  export STATA_MCP__SAVE_HELP=false
  ```

### SECURITY Section

Controls security features.

#### `SECURITY.IS_GUARD`

Enable security guard validation for Stata dofiles.

- **Type**: Boolean
- **Default**: `true`
- **Environment Variable**: `STATA_MCP__IS_GUARD`
- **Description**: When enabled, validates all dofile code against dangerous commands and patterns before execution
- **Example**:
  ```bash
  export STATA_MCP__IS_GUARD=true
  ```

For more details, see [Security Guard Documentation](security.md).

#### Third-Party Ado Installation

MCP exposure of `ado_package_install` is disabled by the default profile because
installed ado packages execute third-party code inside Stata. Exposing it for
MCP requires all of the following:

- Add each approved GitHub `owner/repository` to the exact repository allowlist
- Start the MCP server with `stata-mcp server --unsafe`
- Accept the MCP user-approval prompt for each MCP call

```toml
[SECURITY]
ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES = ["SepineTam/TexIV"]
```

The matching environment variable is
`STATA_MCP__ADO_INSTALL_ALLOWED_GITHUB_REPOSITORIES`. It uses comma-separated
values. SSC and net package names may
contain only ASCII letters and numbers. Net sources must use validated HTTPS
URLs; local paths, IP-address hosts, credentials, queries, fragments, dot
segments, duplicate slashes, and non-default ports are rejected.

The GitHub allowlist validates only the repository name. It does not inspect or
protect the repository contents. Review the repository before installation.

The Python API does not require caller confirmation. CLI calls prompt
interactively unless `-y` or `--yes` is supplied.

### PROJECT Section

Controls project-specific settings.

#### `PROJECT.WORKING_DIR`

Set the working directory for MCP-for-Stata operations.

- **Type**: Path (string)
- **Default**: Current directory (if writable) or `~/Documents`
- **Environment Variable**: `STATA_MCP__CWD` (double underscore)
- **Description**:
  - If set and writable, all output files will be organized under `<WORKING_DIR>/<FOLDER_TAG>/` (default `.statamcp/`)
  - If not set or not writable, falls back to current directory or `~/Documents`
  - **Legacy support**: `STATA_MCP_CWD` (single underscore) is still supported but deprecated
- **Example**:
  ```bash
  export STATA_MCP__CWD="/projects/my-research"
  ```

#### `PROJECT.CLEAN_LOG_DAYS`

Retention window (in days) for Stata logs produced under the working directory.

- **Type**: Integer
- **Default**: `-1` (no cleanup)
- **Environment Variable**: `STATA_MCP__CLEAN_LOG_DAYS`
- **Description**:
  - `-1` disables automatic cleanup
  - When set to a positive integer, the `stata-mcp doctor` cleanup check removes Stata log files older than the specified number of days
- **Example**:
  ```bash
  export STATA_MCP__CLEAN_LOG_DAYS=30
  ```

#### `PROJECT.FOLDER_TAG`

Name of the stata-mcp subdirectory created under `WORKING_DIR`.

- **Type**: String
- **Default**: `.statamcp` (hidden directory)
- **Environment Variable**: `STATA_MCP__FOLDER_TAG`
- **Description**:
  - Determines the folder name used for logs, do-files, results, and temporary files
  - Since v1.16.0 the default was migrated from `stata-mcp-folder` to `.statamcp`
  - To preserve the legacy folder layout, set this to `stata-mcp-folder`
- **Example**:
  ```bash
  export STATA_MCP__FOLDER_TAG=stata-mcp-folder
  ```

The working directory structure:
```
<WORKING_DIR>/<FOLDER_TAG>/        # default: .statamcp/
├── stata-mcp-log/      # Stata execution logs
├── stata-mcp-dofile/   # Generated do-files
├── stata-mcp-result/   # Analysis results
└── stata-mcp-tmp/      # Temporary files
```

**Migration note (v1.16.0)**:
- The default folder name changed from `stata-mcp-folder` to `.statamcp`.
- If an old `stata-mcp-folder` directory is detected under the working directory, MCP-for-Stata writes a `README` notice inside it and creates a `.migrated` marker so the warning is emitted only once.
- To roll back to the previous layout, set `export STATA_MCP__FOLDER_TAG=stata-mcp-folder`.

### MONITOR Section

Controls performance monitoring features.

#### `MONITOR.IS_MONITOR`

Enable RAM monitoring for Stata processes.

- **Type**: Boolean
- **Default**: `false`
- **Environment Variable**: `STATA_MCP__IS_MONITOR`
- **Description**: When enabled, monitors Stata subprocess RAM usage during execution
- **Example**:
  ```bash
  export STATA_MCP__IS_MONITOR=true
  ```

For more details, see [Monitoring Documentation](monitoring.md).

#### `MONITOR.MAX_RAM_MB`

Maximum RAM limit in megabytes.

- **Type**: Integer
- **Default**: `-1` (no limit)
- **Environment Variable**: `STATA_MCP__RAM_LIMIT`
- **Description**:
  - `-1` means no limit (default)
  - When set to a positive value, Stata processes exceeding this limit will be terminated
- **Example**:
  ```bash
  export STATA_MCP__RAM_LIMIT=8192  # 8 GB limit
  ```

### BETA Section

Controls beta/experimental features.

#### `BETA.ENABLE_WRITE_DOFILE`

Control whether the `write_dofile` MCP tool is registered.

- **Type**: Boolean
- **Default**: `false`
- **Environment Variable**: `STATA_MCP__ENABLE_WRITE_DOFILE`
- **Description**:
  - When `false` (default), the `write_dofile` MCP tool is not registered
  - Modern AI agents have native file writing capabilities, making this tool redundant
  - Set to `true` only if you need backward compatibility with older workflows
- **Example**:
  ```bash
  export STATA_MCP__ENABLE_WRITE_DOFILE=true
  ```

> **Note**: This configuration is marked as BETA and may be removed in future versions.

### STATA Section

Controls Stata executable detection.

#### `STATA.STATA_CLI`

Override automatic Stata detection.

- **Type**: Path (string)
- **Default**: Auto-detected based on platform
- **Description**:
  - **macOS**: `/Applications/Stata/StataMP.app/Contents/MacOS/stata-mp`
  - **Windows**: `C:\Program Files\Stata18\StataMP-64.exe`
  - **Linux**: `stata-mp` (from PATH)
- **Example**:
  ```toml
  [STATA]
  STATA_CLI = "/usr/local/stata17/stata-mp"
  ```

### data_info Section

Controls the behavior of the `get_data_info` tool: which descriptive statistics are reported, how strings are summarized, and how cache filenames are constructed.

For `string_keep_number`, `decimal_places`, and `hash_length`, the resolution priority is: explicit argument > environment variable > config file > default.

#### `data_info.metrics`

Default list of numeric metrics returned for each variable.

- **Type**: List of strings
- **Default**: `["obs", "mean", "stderr", "min", "max"]`
- **Description**:
  - Supported values include `obs`, `mean`, `stderr`, `min`, `max`, `q1`, `q3`, `skewness`, and `kurtosis`
  - The default list can be extended with `q1`, `q3`, `skewness`, and `kurtosis` when richer summaries are needed
  - `metrics` is read from the config file only; it does not support environment variables or explicit arguments
- **Example**:
  ```toml
  [data_info]
  metrics = ["obs", "mean", "stderr", "min", "max", "q1", "q3", "skewness", "kurtosis"]
  ```

#### `data_info.string_keep_number`

Maximum number of unique values retained when summarizing string variables.

- **Type**: Integer
- **Default**: `10`
- **Environment Variable**: `STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER`
- **Description**: Categorical strings with more unique values are truncated to this many representatives.
- **Example**:
  ```bash
  export STATA_MCP_DATA_INFO_STRING_KEEP_NUMBER=20
  ```

#### `data_info.decimal_places`

Number of decimal places used when formatting numeric statistics.

- **Type**: Integer
- **Default**: `3`
- **Environment Variable**: `STATA_MCP_DATA_INFO_DECIMAL_PLACES`
- **Example**:
  ```bash
  export STATA_MCP_DATA_INFO_DECIMAL_PLACES=4
  ```

#### `data_info.hash_length`

Length of the hash suffix appended to cached data-info filenames.

- **Type**: Integer
- **Default**: `12`
- **Environment Variable**: `STATA_MCP_DATA_INFO_HASH_LENGTH`
- **Description**: Used by the data-info layer to disambiguate cache entries derived from the same source file.
- **Example**:
  ```bash
  export STATA_MCP_DATA_INFO_HASH_LENGTH=8
  ```

## Using Environment Variables

### Quick Setup

```bash
# Enable debug mode
export STATA_MCP__IS_DEBUG=true

# Set working directory
export STATA_MCP__CWD="/projects/my-analysis"

# Enable monitoring with 8GB RAM limit
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=8192

# Disable security guard (not recommended)
export STATA_MCP__IS_GUARD=false

# Enable console logging
export STATA_MCP__LOGGING_CONSOLE_HANDLER_ON=true
```

### Priority Example

If you set the same option in multiple places:

```bash
# Config file: IS_GUARD = true
# Environment variable: STATA_MCP__IS_GUARD=false
export STATA_MCP__IS_GUARD=false

# Result: Security guard is disabled (environment variable wins)
```

## Configuration Validation

The configuration system includes built-in validation:

- **Boolean values**: Must be `true` or `false` (case-insensitive)
- **Integer values**: Must be valid integers
- **Path values**: Automatically expanded for `~` (home directory)
- **Invalid values**: Fall back to defaults automatically

## Common Configuration Patterns

### Development Setup

```toml
[DEBUG]
IS_DEBUG = true

[DEBUG.logging]
LOGGING_ON = true
LOGGING_CONSOLE_HANDLER_ON = true
LOGGING_FILE_HANDLER_ON = false
```

### Production Setup

```toml
[DEBUG]
IS_DEBUG = false

[DEBUG.logging]
LOGGING_ON = true
LOGGING_CONSOLE_HANDLER_ON = false
LOGGING_FILE_HANDLER_ON = true
MAX_BYTES = 50_000_000
BACKUP_COUNT = 10

[SECURITY]
IS_GUARD = true

[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 16384
```

### High-Performance Computing

```toml
[DEBUG]
IS_DEBUG = false

[DEBUG.logging]
LOGGING_ON = false

[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 65536  # 64 GB
```

## Troubleshooting

### Configuration Not Loading

1. Check if config file exists:
   ```bash
   ls ~/.statamcp/config.toml
   ```

2. Verify TOML syntax:
   ```bash
   python3 -c "import tomllib; tomllib.load(open('~/.statamcp/config.toml', 'rb'))"
   ```

3. Check for environment variable conflicts:
   ```bash
   env | grep STATA_MCP
   ```

### Working Directory Issues

If the working directory is not writable, MCP-for-Stata will fall back to `~/Documents`. To fix:

1. Check directory permissions:
   ```bash
   ls -la /your/working/directory
   ```

2. Create directory with proper permissions:
   ```bash
   mkdir -p /your/working/directory
   chmod u+w /your/working/directory
   ```

### Log Files Not Created

1. Check if logging is enabled:
   ```bash
   echo $STATA_MCP__LOGGING_ON
   ```

2. Verify log file path is writable:
   ```bash
   touch ~/.statamcp/stata_mcp_debug.log
   ```

3. Check disk space:
   ```bash
   df -h
   ```
