# Monitoring System

The monitoring system provides real-time monitoring of Stata processes during execution. This feature is designed to prevent resource exhaustion and improve system stability.

## Overview

The monitoring system is **disabled by default** to maintain 100% backward compatibility. When enabled, it monitors Stata subprocess execution and can automatically terminate processes that exceed configured resource limits.

### Current Features

- **RAM Monitoring**: Track memory usage and terminate processes exceeding RAM limits
- **Cross-Platform**: Works on macOS, Linux, and Windows using `psutil`
- **Non-Invasive**: Minimal overhead when disabled, daemon thread when enabled
- **Extensible**: Abstract base class for adding new monitor types (e.g., timeout monitoring)

## Architecture

### MonitorBase

Abstract base class for all monitor implementations:

```python
class MonitorBase(ABC):
    @abstractmethod
    def start(self, process: Any) -> None:
        """Start monitoring the given process."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop monitoring."""
        pass
```

### RAMMonitor

Monitors RAM usage of Stata processes:

- **Check Interval**: 0.5 seconds
- **Metric**: RSS (Resident Set Size) in MB
- **Action**: Kills process when limit exceeded
- **Error**: Raises `RAMLimitExceededError` with details

## Configuration

### Enable Monitoring

Monitoring is controlled by two configuration options:

#### Option 1: Configuration File

Edit `~/.statamcp/config.toml`:

```toml
[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 8192  # 8 GB limit
```

#### Option 2: Environment Variables

```bash
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=8192
```

### Configuration Priority

1. Environment variables (highest)
2. Config file (`~/.statamcp/config.toml`)
3. Default values (lowest)

### RAM Limit Values

- `-1` or `None`: No limit (default)
- `0`: Not recommended (will kill immediately)
- Positive value: RAM limit in MB

Examples:
```bash
# No limit (default)
export STATA_MCP__RAM_LIMIT=-1

# 4 GB limit
export STATA_MCP__RAM_LIMIT=4096

# 8 GB limit
export STATA_MCP__RAM_LIMIT=8192

# 16 GB limit
export STATA_MCP__RAM_LIMIT=16384
```

## Usage

### Basic Setup

1. **Enable monitoring in config**:
   ```bash
   export STATA_MCP__IS_MONITOR=true
   export STATA_MCP__RAM_LIMIT=8192
   ```

2. **Run MCP-for-Stata normally**:
   ```bash
   stata-mcp
   ```

3. **Monitoring is automatic** when enabled:
   - No code changes needed
   - Works with all MCP tools
   - Integrates seamlessly with existing workflows

### Programmatic Usage

If you're using MCP-for-Stata as a library:

```python
from stata_mcp.monitor import RAMMonitor
from stata_mcp.core.stata import StataDo

# Create monitor with 8GB limit
monitor = RAMMonitor(max_ram_mb=8192)

# Pass to StataDo
stata = StataDo(
    dofile_path="analysis.do",
    monitors=[monitor]  # Optional: list of monitors
)

# Execution is automatically monitored
result = stata.execute()
```

## Behavior

### When RAM Limit is Exceeded

1. **Detection**: Monitor detects RAM usage > limit
2. **Logging**: Warning logged with details
3. **Termination**: Process is killed immediately
4. **Error**: `RAMLimitExceededError` is raised

### Example Output

```
WARNING: RAM limit exceeded: 8256MB > 8192MB. Killing Stata process (PID: 12345)
ERROR: RAM limit exceeded: Used 8256MB, Limit 8192MB
```

### Normal Completion

If process finishes before exceeding limit:
- Monitor stops gracefully
- No errors raised
- Normal execution flow continues

## Performance Considerations

### Overhead

- **Disabled**: Zero overhead (default)
- **Enabled**: Minimal overhead from daemon thread
  - One RAM check every 0.5 seconds
  - Uses `psutil` for cross-platform compatibility

### Recommendations

For **production environments**:
```toml
[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 16384  # Set reasonable limit for your hardware
```

For **development environments**:
```toml
[MONITOR]
IS_MONITOR = false  # Disable to avoid accidental termination
```

For **high-performance computing**:
```toml
[MONITOR]
IS_MONITOR = true
MAX_RAM_MB = 65536  # 64 GB for large datasets
```

## Error Handling

### RAMLimitExceededError

Raised when RAM limit is exceeded:

```python
from stata_mcp.core.types import RAMLimitExceededError

try:
    result = stata.execute()
except RAMLimitExceededError as e:
    print(f"RAM exceeded: {e.ram_used_mb:.0f}MB > {e.ram_limit_mb}MB")
    # Handle error: save work, notify user, etc.
```

Error attributes:
- `ram_used_mb`: Actual RAM used when limit exceeded
- `ram_limit_mb`: Configured RAM limit

## SMCL Log Expansion Limits

SMCL (Stata Markup and Control Language) logs can contain tags such as `{space N}` and `{hline N}` that expand into repeated spaces or dashes. A malformed or malicious log with an extremely large `N` could cause the parser to allocate excessive memory while converting SMCL to plain text.

To prevent this, the SMCL parser applies a hard upper bound to every expansion:

- **Maximum expansion**: 10,000 characters per tag
- **Affected tags**: `{space N}`, `{hline N}`
- **Default fallback**: `{hline}` without a count expands to 13 dashes

This limit is applied automatically whenever SMCL logs are read through the `read_log` tool or when SMCL output is enabled via `--enable-smcl true`. It is not configurable and is independent of the RAM monitor, but serves the same goal of preventing resource exhaustion.

## Extensibility

### Creating Custom Monitors

You can create custom monitors by extending `MonitorBase`:

```python
from stata_mcp.monitor.base import MonitorBase
import time
import threading

class TimeoutMonitor(MonitorBase):
    """Monitor and timeout long-running processes."""

    def __init__(self, timeout_seconds: int):
        self.timeout = timeout_seconds
        self._start_time = None
        self._monitor_thread = None
        self._stop_event = threading.Event()

    def start(self, process):
        """Start timeout monitoring."""
        self._start_time = time.time()
        self.process = process

        def monitor_loop():
            while not self._stop_event.is_set():
                if time.time() - self._start_time > self.timeout:
                    self.process.kill()
                    break
                self._stop_event.wait(1)

        self._monitor_thread = threading.Thread(
            target=monitor_loop,
            daemon=True
        )
        self._monitor_thread.start()

    def stop(self):
        """Stop monitoring."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
```

### Using Multiple Monitors

You can use multiple monitors simultaneously:

```python
from stata_mcp.monitor import RAMMonitor, TimeoutMonitor

# Create multiple monitors
ram_monitor = RAMMonitor(max_ram_mb=8192)
timeout_monitor = TimeoutMonitor(timeout_seconds=3600)

# Pass to StataDo
stata = StataDo(
    dofile_path="analysis.do",
    monitors=[ram_monitor, timeout_monitor]
)
```

## Troubleshooting

### Monitor Not Working

1. **Check if monitoring is enabled**:
   ```bash
   echo $STATA_MCP__IS_MONITOR
   ```

2. **Verify config file syntax**:
   ```bash
   cat ~/.statamcp/config.toml
   ```

3. **Check for environment variable conflicts**:
   ```bash
   env | grep STATA_MCP
   ```

### Process Killed Unexpectedly

1. **Check RAM limit is reasonable**:
   ```bash
   echo $STATA_MCP__RAM_LIMIT
   ```

2. **Review logs for termination reason**:
   ```bash
   tail -f ~/.statamcp/stata_mcp_debug.log
   ```

3. **Increase limit if needed**:
   ```bash
   export STATA_MCP__RAM_LIMIT=16384
   ```

### psutil Issues

If you encounter `psutil` errors:

1. **Ensure psutil is installed**:
   ```bash
   uv pip install psutil>=6.0.0
   ```

2. **Check psutil version**:
   ```bash
   python3 -c "import psutil; print(psutil.__version__)"
   ```

3. **Verify process access permissions** (Linux/macOS):
   ```bash
   # Monitor should have access to child processes
   # No special action needed for child processes
   ```

## Best Practices

### 1. Start with No Limit

For initial testing:
```bash
export STATA_MCP__IS_MONITOR=true
export STATA_MCP__RAM_LIMIT=-1  # No limit initially
```

### 2. Monitor Typical Usage

Run typical workloads and observe RAM usage in logs.

### 3. Set Reasonable Limit

Set limit 20-50% above typical usage:
```bash
# If typical usage is 6GB
export STATA_MCP__RAM_LIMIT=8192  # 8GB limit
```

### 4. Test Edge Cases

Test with large datasets to ensure limit is appropriate.

### 5. Document Limits

Document RAM limits in project documentation for team members.

## Security Considerations

- Monitor runs in daemon thread (terminated when main thread exits)
- No privilege escalation required
- Uses standard `psutil` library for cross-platform compatibility
- Monitor only has access to child processes it creates

## Future Enhancements

Potential future monitor types:
- **Timeout Monitor**: Limit execution time
- **CPU Monitor**: Track CPU usage percentage
- **Disk I/O Monitor**: Monitor disk read/write operations
- **Network Monitor**: Track network activity (if applicable)

## Notes

- This feature was developed with assistance from Claude Code and GLM-4.7
- Monitoring is **opt-in** via configuration
- When disabled, behavior is 100% identical to previous versions
- Monitor system designed for extensibility to support future use cases
