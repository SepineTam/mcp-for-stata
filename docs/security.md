# Security Guard System

The Security Guard system provides protection against dangerous commands and operations in Stata dofiles. It acts as a safety layer between LLM-generated code and actual execution.

## Overview

The Security Guard is **enabled by default** to prevent accidental execution of destructive operations. It validates all dofile code against a blacklist of dangerous commands and patterns before execution.

### Key Features

- **Blacklist-Based Validation**: Blocks known dangerous commands
- **Pattern Matching**: Detects potentially dangerous operations using regex
- **Line-by-Line Analysis**: Provides detailed risk reporting with line numbers
- **Configurable**: Can be disabled if needed (not recommended)
- **Zero False Positives for Safe Code**: Only flags genuinely dangerous operations

## Dangerous Commands

The Security Guard blocks the following dangerous commands. Stata resolves any unambiguous prefix to its full command (for example `sh` to `shell`), so the blacklist enumerates both the full names and the minimum abbreviations that Stata accepts. `GuardValidator` matches both forms before execution.

### Shell Execution Commands

| Command | Abbreviation | Description | Example |
|---------|--------------|-------------|---------|
| `!` | - | Unix-style shell escape | `! ls -la` |
| `!!` | - | Extended shell command | `!! vi file.do` |
| `shell` | `sh` | Shell command execution | `shell dir` |
| `xshell` | `xsh` | Extended shell for Mac/Unix (GUI) | `xshell vi file.do` |
| `winexec` | `winex` | Windows program execution | `winexec notepad.exe` |
| `unixcmd` | `unixc` | Unix command execution (macOS/Linux) | `unixcmd ls` |

### File Operations

| Command | Abbreviation | Description | Risk |
|---------|--------------|-------------|------|
| `erase` | `era` | File deletion | Data loss |
| `rm` | - | File deletion (alias) | Data loss |
| `rmdir` | `rmd` | Directory removal | Data loss |
| `copy` | - | File copy | Can overwrite files |

### Code Execution

| Command | Description | Risk |
|---------|-------------|------|
| `run` | Run another do-file | Untrusted code execution |
| `do` | Execute do-file | Untrusted code execution |
| `include` | Include another do-file | Untrusted code execution |

### Package Management

Direct package-management commands submitted through `stata_do` cannot execute
`ssc`, `net`, `github`, `adoupdate`, or `update`. This separate boundary is
always active, even when the general Guard is disabled. Approved third-party
installation must use `ado_package_install`.

## Dofile Directory Boundary

Since v1.16.2, `stata_do` rejects any dofile that resolves outside an approved root directory. The boundary check runs before the Guard validator and applies to both the MCP server and the CLI `stata-mcp tool do` entry point.

### Allowed Roots

A dofile is accepted only when its resolved absolute path lies under one of the following directories:

| Root | Source |
|------|--------|
| `<WORKING_DIR>/<FOLDER_TAG>/stata-mcp-dofile/` | `STATA_MCP_FOLDER.DO` |
| `<WORKING_DIR>` | Configured working directory |

`WORKING_DIR` is taken from `STATA_MCP__CWD` (or the legacy `STATA_MCP_CWD`); the dofile root is the `stata-mcp-dofile/` subdirectory under it. Symbolic links are resolved before the check, so a link pointing outside the allowed roots is denied.

### Rejection Behaviour

When the resolved path is outside the allowed roots, `stata_do` returns an error of the form `Access denied: Dofile '<path>' is outside allowed directories.` together with the list of allowed roots, and a `[SECURITY VIOLATION]` warning is written to the log with the requested path, the resolved path, and the configured roots.

### Operational Guidance

Place dofiles either under the configured working directory or let MCP-for-Stata generate them into `stata-mcp-dofile/`. To execute dofiles that live elsewhere, point `STATA_MCP__CWD` at a parent directory that already contains them rather than relaxing the check.

## Data Info Access Boundary

`get_data_info` accepts local paths and URL data sources. Local paths are always validated before any data handler is invoked. URL sources keep the historical unrestricted behavior unless the beta URL guard is explicitly enabled.

### Local Data Files

Local data files must resolve under the configured `WORKING_DIR`. Relative paths are resolved against `WORKING_DIR`, so examples such as `./data/survey.dta` are portable when the working directory is the project root. Absolute paths outside `WORKING_DIR` are rejected and a `[SECURITY VIOLATION]` warning is written to the log.

### URL Data Sources

By default, URL data sources are passed through to the data handler without scheme, host, userinfo, or domain checks.

When `[BETA] enable_data_info_url_guard=true`, URL data sources are checked before any request is made:

- The scheme must be `https`
- IP-address hosts are rejected
- URL userinfo such as `https://user:pass@example.com/file.csv` is rejected
- The URL hostname must match `data_info_allowed_url_domains`

Allowlist entries match the exact hostname and subdomains; add `raw.githubusercontent.com` explicitly when raw GitHub content is required. Rejected URL requests return an access-denied message and write a `[SECURITY VIOLATION]` audit log entry with the sanitized URL and rejection reason.

## Local Macro Expansion Detection

A naive blacklist that only inspects each line's first token can be bypassed by hiding a dangerous command inside a local macro and expanding it later. Since v1.16.2 `GuardValidator` performs a two-pass check that closes this gap.

### Detection Logic

1. Pass one collects every `local <name> "<value>"` (and `local <name> = "<value>"`) definition. When the trimmed value is itself in `DANGEROUS_COMMANDS`, the local name is added to a tainted set.
2. Pass two scans every non-comment line for `` `name' `` expansions of any tainted local and records each match as a `macro` risk in the `SecurityReport`.

The local name pattern is `\w+`, so suffixed or prefixed variants such as `local cmd_x "shell"` are tracked alongside plain names. Stata prefixes (`capture`, `quietly`, `noisily`, ...) are stripped before both passes, so they cannot mask a tainted definition.

### Counter-Example

```stata
local cmd_x "shell"
`cmd_x' rm -rf /tmp/important
```

Without macro tracking the second line begins with a backtick and would slip past a first-token check. With macro tracking enabled the validator reports a `macro` risk on the second line, and `stata_do` refuses execution.

### Coverage Caveats

The macro tracker matches single-token dangerous values only. Concatenated assignments such as `local cmd = "she" + "ll"` or values constructed at runtime are outside its scope and remain a known limitation of static validation. Keep the Guard enabled and review generated dofiles when external sources contribute their content.

## Guard Disable Warning

`STATA_MCP__IS_GUARD=false` (or `[SECURITY] IS_GUARD = false` in `~/.statamcp/config.toml`) disables the general validator. Disabling the Guard skips its blacklist, pattern, and macro checks. Each `stata_do` call emits the warning `[SECURITY] Guard is disabled. Dangerous dofile commands will not be blocked.` to the log; the same line is recorded at server startup when the configuration is read.

Disable the Guard only inside controlled environments such as the Docker sandbox installation or an ephemeral VM, and re-enable it once the trusted task completes. The directory boundary and package-management boundary continue to apply even when the general Guard is disabled.

## Third-Party Ado Installation Boundary

Installing an ado package executes third-party code inside Stata, so it is
protected independently from the dofile Guard:

1. The default `all` MCP profile does not expose `ado_package_install`; the
   operator must explicitly start `stata-mcp server --unsafe`.
2. SSC and net package names may contain only ASCII letters and numbers.
   GitHub repositories must use `owner/repository` format and match the exact
   GitHub repository allowlist. Net sources must use validated HTTPS URLs.
3. Every MCP call requires client-mediated user elicitation. CLI calls prompt
   interactively unless `-y` or `--yes` is supplied. The Python API performs
   validation but does not require enablement or confirmation.
4. The installer validates again immediately before sending the command to
   Stata. GitHub helper installation and help-cache refresh are never implicit.
5. Direct package-management commands submitted through `stata_do` are blocked,
   even when the general dofile Guard is disabled.

These MCP controls are cumulative. Disabling the dofile Guard does not bypass
the unsafe profile, GitHub allowlisting, or MCP confirmation. Disabling the general
Guard still permits other dangerous execution paths and is not a security
boundary.

GitHub allowlisting validates only the repository name and provides no
content-level security protection. Review the repository before installation.
Remote sources may change; the current installer does not pin package versions
or verify hashes or signatures.

## Configuration

### Enable/Disable Security Guard

#### Option 1: Configuration File

Edit `~/.statamcp/config.toml`:

```toml
[SECURITY]
IS_GUARD = true  # Default: true
```

#### Option 2: Environment Variable

```bash
# Enable (default)
export STATA_MCP__IS_GUARD=true

# Disable (not recommended)
export STATA_MCP__IS_GUARD=false
```

### Default Behavior

- **Default**: Enabled (`IS_GUARD = true`)
- **Recommended**: Keep enabled for production use
- **Development**: Can be disabled for testing (use with caution)

## Usage

### Basic Usage

The Security Guard is automatically applied when using the `stata_do` tool:

```python
# When IS_GUARD is enabled (default)
result = stata_mcp.stata_do(code="""
    sysuse auto
    regress price mpg weight
""")

# Safe code executes normally
```

### Security Validation Example

When dangerous code is detected:

```python
result = stata_mcp.stata_do(code="""
    sysuse auto
    ! rm -rf /  # Dangerous command
""")

# Error: Security validation failed
# ❌ Security validation failed. Found dangerous items:
#   - Line 3: command '!'
```

### Programmatic Usage

If you're using MCP-for-Stata as a library:

```python
from stata_mcp.guard import GuardValidator

# Create validator
validator = GuardValidator()

# Validate code
code = """
sysuse auto
regress price mpg weight
"""

report = validator.validate(code)

if report.is_safe:
    print("✅ Code is safe to execute")
else:
    print(f"❌ Found {len(report.dangerous_items)} dangerous items:")
    for item in report.dangerous_items:
        print(f"  {item}")
```

## Security Report

### SecurityReport Object

```python
@dataclass
class SecurityReport:
    is_safe: bool                              # True if no dangerous items found
    dangerous_items: List[RiskItem]            # List of detected risks
```

### RiskItem Object

```python
@dataclass
class RiskItem:
    type: str                                  # "command" or "pattern"
    content: str                               # The dangerous content
    line: int                                  # Line number (1-indexed)
```

### Example Output

```python
# Safe code
report = validator.validate("sysuse auto")
print(report)
# Output: ✅ Code passed security validation

# Dangerous code
report = validator.validate("! rm file.txt")
print(report)
# Output:
# ❌ Security validation failed. Found dangerous items:
#   - Line 1: command '!'
```

## Dangerous Patterns

The Security Guard uses regex patterns to detect dangerous operations:

### Shell Command Patterns

```python
r"!\s*\w+"           # Shell escape with command: ! ls
r"!!\s*\w+"          # Extended shell: !! vi file.do
r"shell\s+\w+"       # Shell command: shell dir
r"xshell\s+\w+"      # Extended shell: xshell vi file.do
r"winexec\s+\S+"     # Windows execution: winexec program.exe
r"unixcmd\s+\w+"     # Unix command: unixcmd ls
```

### File Operation Patterns

```python
r"erase\s+.*"        # File deletion: erase file.dta
r"rm\s+.*"           # File deletion: rm file.dta
r"rmdir\s+.*"        # Directory removal: rmdir mydir
r"copy\s+.*"         # File copy: copy file1.dta file2.dta
```

### Code Execution Patterns

```python
r"run\s+.*"          # Run do-file: run script.do
r"\bdo\s+.*"         # Execute do-file: do script.do
r"include\s+.*"      # Include do-file: include setup.do
```

## Validation Process

### Step-by-Step Validation

1. **Code Input**: Receive dofile code string
2. **Line Split**: Split code into lines for line number tracking
3. **Filtering**: Skip empty lines and comments (starting with `*`)
4. **Command Check**: Check each line against dangerous commands
5. **Pattern Check**: Check each line against dangerous patterns
6. **Report Generation**: Create SecurityReport with all findings

### Example Validation

```python
code = """
* This is a comment
sysuse auto
! rm dangerous.txt  # Line 3
regress price mpg
"""

report = validator.validate(code)
# Report:
# ❌ Security validation failed. Found dangerous items:
#   - Line 3: command '!'
```

## Best Practices

### 1. Keep Security Guard Enabled

```toml
[SECURITY]
IS_GUARD = true  # Always keep enabled
```

### 2. Review Security Reports

Always review security validation reports:

```python
report = validator.validate(code)
if not report.is_safe:
    # Log or notify about dangerous items
    for item in report.dangerous_items:
        logger.warning(f"Dangerous item found: {item}")
```

### 3. Use Whitelist for Allowed Operations

If you need to execute certain dangerous operations:

1. Review the code manually
2. Remove dangerous commands
3. Use safe alternatives

Example:
```stata
* Instead of: ! rm tempfile.dta
* Use: erase tempfile.dta  (still blocked, but shows intent)

* Better approach: Use Stata's built-in safe operations
capture erase tempfile.dta
```

### 4. Educate Users

Document which commands are blocked and why:

```markdown
## Blocked Commands

The following commands are blocked for security reasons:
- Shell commands (!, shell, xshell, etc.)
- File deletion (erase, rm)
- External code execution (run, do, include)

Please use safe alternatives or contact administrator for assistance.
```

## Troubleshooting

### False Positives

If you believe a command is incorrectly flagged:

1. **Review the command**: Is it actually dangerous?
2. **Check for patterns**: Does it match a dangerous pattern?
3. **Consider alternatives**: Is there a safer way to accomplish the task?

### Disabling Security Guard

**⚠️ Warning**: Disabling the Security Guard is not recommended.

Only disable if:
- You're in a trusted environment
- All code is manually reviewed
- You understand the risks

```bash
# Temporary disable (current session only)
export STATA_MCP__IS_GUARD=false
stata-mcp

# Permanent disable (add to config)
# Edit ~/.statamcp/config.toml
[SECURITY]
IS_GUARD = false
```

### Customizing Blacklist

You can extend the blacklist by modifying the code:

```python
from stata_mcp.guard.blacklist import DANGEROUS_COMMANDS

# Add custom dangerous commands
DANGEROUS_COMMANDS.add("my_dangerous_command")

# Use custom validator
from stata_mcp.guard import GuardValidator
validator = GuardValidator()
validator.dangerous_commands.add("another_command")
```

## Security Considerations

### What the Guard Protects Against

✅ **Prevents**:
- Shell command execution
- File deletion operations
- Untrusted code execution
- System-level operations

❌ **Does Not Prevent**:
- Data modification within Stata
- Infinite loops
- Memory exhaustion
- Stata crashes

### Limitations

The Security Guard:
- Does not analyze data flow
- Does not track variable values
- Does not prevent resource exhaustion
- Is not a substitute for proper code review

### Defense in Depth

The Security Guard is one layer of protection. Combine with:

1. **Monitoring**: Enable RAM monitoring (see [Monitoring Documentation](monitoring.md))
2. **Sandboxing**: Use isolated environments for untrusted code
3. **Code Review**: Manually review generated code
4. **Backups**: Maintain regular backups of important data

## Integration with MCP Tools

### Automatic Integration

The Security Guard is automatically integrated with:

- `stata_do`: Execute Stata do-files (validated by default)
- `write_dofile`: Create do-files (not validated until execution)

### Validation Flow

```
User Request → MCP Tool → Security Guard → Validation
                                      ↓
                                 Pass? → Execute
                                      ↓
                                 Fail? → Return Error
```

## Extensibility

### Creating Custom Validators

You can create custom validators for specific use cases:

```python
from stata_mcp.guard import GuardValidator, RiskItem, SecurityReport

class CustomValidator(GuardValidator):
    """Custom validator with additional rules."""

    def validate(self, code: str) -> SecurityReport:
        # Get base validation results
        report = super().validate(code)

        # Add custom validation logic
        if "custom_dangerous_thing" in code:
            report.dangerous_items.append(
                RiskItem(
                    type="custom",
                    content="custom_dangerous_thing",
                    line=code.find("custom_dangerous_thing")
                )
            )
            report.is_safe = False

        return report
```

### Combining Multiple Validators

```python
from stata_mcp.guard import GuardValidator

# Create multiple validators
basic_validator = GuardValidator()
custom_validator = CustomValidator()

# Validate with both
code = "some stata code"
report1 = basic_validator.validate(code)
report2 = custom_validator.validate(code)

# Combine results
if report1.is_safe and report2.is_safe:
    print("✅ All validations passed")
```

## Examples

### Example 1: Safe Code Execution

```python
from stata_mcp.guard import GuardValidator

validator = GuardValidator()

safe_code = """
* Load sample data
sysuse auto

* Run regression
regress price mpg weight

* Display results
display "R-squared: " + string(e(r2))
"""

report = validator.validate(safe_code)
print(report)
# Output: ✅ Code passed security validation
```

### Example 2: Dangerous Code Detection

```python
dangerous_code = """
sysuse auto

* This will be blocked
! rm -rf /important/data

regress price mpg
"""

report = validator.validate(dangerous_code)
print(report)
# Output:
# ❌ Security validation failed. Found dangerous items:
#   - Line 5: command '!'
```

### Example 3: Multiple Violations

```python
multiple_violations = """
sysuse auto
shell delete file.txt
run untrusted_script.do
"""

report = validator.validate(multiple_violations)
print(f"Found {len(report.dangerous_items)} violations:")
for item in report.dangerous_items:
    print(f"  {item}")
# Output:
# Found 2 violations:
#   Line 3: command 'shell'
#   Line 4: pattern 'run\s+.*'
```

## Summary

The Security Guard system provides essential protection for automated Stata execution:

- ✅ **Enabled by default** for safety
- ✅ **Blocks dangerous commands** (shell, file deletion, etc.)
- ✅ **Pattern-based detection** for comprehensive coverage
- ✅ **Detailed reporting** with line numbers
- ✅ **Configurable** for different use cases
- ✅ **Zero overhead** when disabled (not recommended)

For production use, always keep the Security Guard enabled and review validation reports regularly.
