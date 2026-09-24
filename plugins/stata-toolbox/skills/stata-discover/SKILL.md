---
name: stata-discover
description: Use this skill when you need to find Stata on the user's machine or configure `stata-mcp` to use it. `stata-discover` provides the workflow for discovering Stata executables and the official way to configure `stata-mcp`. If the user's computer has multiple Stata executables available, this skill also provides the version the user most likely wants to use.
metadata: 
  version: "0.1.0"
---

Users need Stata to run `stata-mcp`, but Stata is not always installed in a default location. This skill discovers which Stata executables/versions exist on the user's device and configures `stata-mcp` to use the most suitable one.

All commands below use `uvx stata-mcp`; if `stata-mcp` is already installed, the bare `stata-mcp` command works the same way.

# Stata Discover

## When to Use

- First-time setup: the user has not configured Stata for `stata-mcp` yet
- `stata_do` or `stata-mcp doctor` reports that the Stata CLI cannot be found
- The user wants to switch the Stata version/edition used by `stata-mcp`
- The machine has multiple Stata installations and the user is unsure which one is in use

## Find Stata with CLI

List all Stata installations on the machine:

```bash
uvx stata-mcp discover
```

- Prints one discovered Stata path per line, deduplicated and sorted; prints nothing when none is found
- Search scope: installed applications, common installation directories, `PATH`, and the `STATA_CLI` environment variable
- Read-only: does not launch Stata, verify licenses, or modify configuration
- Available since v1.24.0; macOS / Windows only (reports OSNotSupported on Linux — Linux users should rely on auto-detection below or set the path manually)
- Note: on macOS the output is a `.app` bundle path (e.g. `/Applications/StataNow/StataMP.app`), but `STATA_CLI` requires the CLI binary inside the bundle: append `/Contents/MacOS/<binary>`, where `<binary>` is usually `stata-<edition>` such as `stata-mp` (StataNow bundles may name it `StataMP` instead — check the directory). Full example: `/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp`

Independently, Stata-MCP ships a built-in `StataFinder` (`src/stata_mcp/stata/stata_finder/`). When `STATA_CLI` is not configured, it automatically discovers the best Stata executable and caches the result into the config file — no manual step needed.

Search locations per platform:

| Platform | Search locations |
|---|---|
| macOS | `/usr/local/bin` (stata-mp / stata-se / stata-be / stata); `Stata*.app` under `/Applications` and `~/Applications` (version read from the `isstata.*` file inside the app) |
| Windows | `Stata*` directories under `Program Files` and `Program Files (x86)` on `C:\` and `D:\`, plus other available drives |
| Linux | `/usr/local/bin` and its subdirectories whose names contain "stata" |

When multiple Stata installations exist, auto-detection picks by:

1. Edition first: `mp` > `se` > `be` > `ic` > `default`
2. Then version number within the same edition, higher wins (float versions like `19.5` are supported; an undetectable version counts as 99, i.e. treated as the current default version)

Inspect the currently resolved Stata CLI:

```bash
uvx stata-mcp config show cli           # value persisted in the config file
uvx stata-mcp doctor --check stata_cli  # effective path and its source (from env / from config / auto-detected)
```

After picking a version from the `discover` list, persist it with `uvx stata-mcp config set cli <path>` (see the next section).

## Configure Stata for Stata-MCP

At runtime, Stata-MCP resolves `STATA_CLI` in this order: config file > `STATA_CLI` environment variable > auto-detection (the detected result is written back to the user config file as a cache to speed up later startups).

### Permanent (recommended)

```bash
uvx stata-mcp config set cli            # auto-detect the best edition and persist it
uvx stata-mcp config set cli /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp  # macOS example
uvx stata-mcp config set cli "C:\Program Files\Stata18\StataMP-64.exe"                   # Windows example
uvx stata-mcp config edit STATA.STATA_CLI /path   # modify an existing config entry
```

This writes to the `[STATA]` section of `~/.statamcp/config.toml` and applies to all projects.

### Project-level

Create `.statamcp/config.toml` in the project root:

```toml
[STATA]
STATA_CLI = "/path/to/stata-mp"
```

For ordinary settings the project file overrides the user file, which suits projects that must pin a specific Stata version.

### Temporary

Use the `STATA_CLI` environment variable, effective for the current command only:

```bash
STATA_CLI=/path/to/stata-mp uvx stata-mcp doctor
```

Caveat: if `STATA_CLI` is already persisted in a config file, the runtime prefers the config file value and the environment variable has no effect. Before relying on a temporary override, confirm with `uvx stata-mcp config show cli` that the config file has no value, or use `config set cli` instead.

### Reset to auto-detection

There is no `config unset` command. To return to auto-detection, manually remove the `STATA_CLI` key from the `[STATA]` section of `~/.statamcp/config.toml` (and any project-level `.statamcp/config.toml`).

## Verify

### General check: doctor

```bash
uvx stata-mcp doctor
```

The command is identical on Windows / macOS / Linux. Doctor runs 12 checks (os, python, uv, dependencies, stata_cli, stata_execution, config, working_dir, guard, monitor, pypi, cleanup). Useful flags:

- `--check stata_cli --check stata_execution`: run only Stata-related checks (`--check` is repeatable)
- `--verbose`: show details of each check
- `--json`: machine-readable output

### Real execution check

Doctor's `stata_execution` check actually launches Stata and runs `display "Stata-MCP Doctor Test"` and `exit, STATA` (stdin pipe on Unix, `/e do` batch mode on Windows, 15-second timeout on both). A pass means the Stata CLI can execute commands.

For an end-to-end verification, run a real do-file:

```bash
uvx stata-mcp tool do path/to/test.do
```

Or call the `stata_do` tool from an MCP client (run `uvx stata-mcp install` first to write the client config, and restart the client after the first-time setup).

## Troubleshooting

- **`discover` prints nothing**: Stata is likely installed in a non-standard location. Ask the user for the installation path, verify the binary exists and is executable, then `config set cli <path>`.
- **Doctor `stata_cli` FAILs**: no usable path from env, config, or auto-detection — set one via `config set cli` or `STATA_CLI`.
- **Doctor `stata_execution` times out (>15s)**: usually a license dialog or first-launch prompt blocking Stata startup. Open the Stata GUI once to complete activation, then re-run doctor.
- **Environment variable seems ignored**: a persisted config file value wins at runtime; check `config show cli` and clear it if needed (see "Reset to auto-detection").
