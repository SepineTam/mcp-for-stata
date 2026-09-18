# Installation

This guide takes you from choosing an installation method to confirming that
your AI client can run Stata. For a first installation, use the `uvx` route below.

## Before you start

- Install and license Stata on this computer. Confirm that Stata itself can run a command.
- Install the AI client you want to use, such as Claude Code, Codex or Cursor.
- The recommended route requires [uv](https://docs.astral.sh/uv/getting-started/installation/), which provides `uvx`. Python-package and source installations require Python 3.11 or later.
- Allow network access to the package index and GitHub. Stata and its license are not included with MCP-for-Stata.

Getting the program and configuring a client are separate steps. `uvx` manages
the program's Python environment; `stata-mcp install` writes the client setup
and installs supported optional components. It does not install the AI client.

## Choose a method

| Method | Best suited to | What it does |
|---|---|---|
| Ask your agent | Users who prefer natural-language setup | The agent follows this guide using its available terminal/file tools |
| `uvx` command (recommended) | Most users | Runs the installer without manually managing a Python environment |
| Installation script | Machines that do not have uv yet | Checks for uv, offers to install it, then runs the client installer |
| Claude Code native plugin | Claude Code users who want plugin-managed components | Installs `stata-toolbox` through the Claude marketplace |
| Manual client configuration | Custom launch commands, project scope or other clients | Registers the MCP server through the client's UI, CLI or config file |
| Persistent package, executable or source | Regular CLI use and development | Provides a local program that you can run or register manually |

### Ask your agent

Copy this into an agent that can use your local terminal and edit configuration:

```text
Read docs/install.md in the SepineTam/mcp-for-stata GitHub repository.
Install MCP-for-Stata for the AI client I am using, with the default Stata
addons and without extras. Check the Stata executable, preserve my existing
configuration, and tell me which components were installed or skipped.
After I restart the client, help me verify it with Stata's auto example data.
```

The agent may need you to identify the client or approve its local operations.
Restarting the client and supplying a valid Stata installation remain necessary.

## Recommended: install with uvx

### 1. Check uv and Stata

```bash
uv --version
uvx stata-mcp doctor --check stata_cli
```

If uv is missing, follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)
or use the installation scripts below. If Stata is not found, set the full path
to its executable, not a directory or shortcut:

```bash
uvx stata-mcp config set cli "/absolute/path/to/stata-executable"
uvx stata-mcp doctor --check stata_cli
```

On macOS and Windows, `uvx stata-mcp discover` can list installation candidates.
Discovery identifies files; it does not verify your Stata license or run an analysis.

### 2. Choose your client

Run the command for the client you use:

```bash
uvx stata-mcp install -c codex
uvx stata-mcp install -c cc
uvx stata-mcp install -c cursor
```

`cc` means Claude Code; `claude` means Claude Desktop. Other client IDs and
aliases are listed in the [CLI reference](cli.md#install-to-ai-clients).
To configure all installer targets, use:

```bash
uvx stata-mcp install --all
```

Bare `install` has the same meaning as `install --all`; it does not select only
the clients already installed on the machine. Pi is excluded from `--all` because
it requires a separate MCP adapter. Use `-c pi` explicitly for that integration.
Claude Desktop is not an installation target on Linux.

### 3. Choose optional components

The default is Stata MCP plus supported Stata addons. Extras are opt-in.

| Command suffix | Components requested |
|---|---|
| `install -c codex` | Base MCP + addon |
| `install -c codex --no-addon` | Base MCP only |
| `install -c codex --with-extra` | Base MCP + addon + extra |
| `install -c codex --no-addon --with-extra` | Base MCP + extra |

Prefix these commands with `uvx stata-mcp`. The same switches apply to `--all`.

- **addon** comes from GitHub `plugins/stata-toolbox/`: Stata skills, writing rules and LSP configuration where supported.
- **extra** comes from GitHub `plugins/external/`: research MCP definitions such as DIP, NBER and Zotero, plus skills added to that directory.

Each installation resolves GitHub `master` to a fixed commit before downloading
the selected directories. Skills include their scripts, references and assets.
The installer records source commits and hashes, upgrades its unchanged files,
and skips files that you have modified. A download failure keeps the base MCP
configuration and produces a warning.

Support varies by client: Claude Code supports the supplied rules and LSP setup;
other clients may receive skills and MCP configuration only. LSP setup requires
the language-server program on PATH. Extra MCP configuration does not install
or log in to Zotero or any other third-party application. See the
[component support table](cli.md#install-options) for exact coverage.

## Installation scripts

Download the appropriate file from the repository's
[scripts directory](https://github.com/SepineTam/mcp-for-stata/tree/master/scripts).
These scripts check for uv, offer to install it if needed, and call
`uvx stata-mcp install`. With no client argument they use `--all`.

| System | Script | How to use it |
|---|---|---|
| macOS | `install.command` | Double-click in Finder, or run from Terminal |
| macOS / Linux | `install.sh` | `bash install.sh -c codex` |
| Windows | `install.bat` | Double-click from File Explorer |
| Windows PowerShell | `install.ps1` | `./install.ps1 -Client codex` |

If macOS asks for execute permission, run `chmod +x install.command` on the
downloaded file. If Windows blocks the script, review the file and your local
execution policy rather than changing system-wide policy indiscriminately.

The wrapper scripts have their own client list and arguments. For newer client
IDs, `--with-extra`, `--no-addon` or a fixed component version, use the `uvx`
installer command directly after uv is available.

## Claude Code native plugin

This is an alternative way to manage Claude Code's Stata integration through
its plugin manager:

```bash
claude plugin marketplace add SepineTam/mcp-for-stata
claude plugin install stata-toolbox@stata-plugin-lib --scope user
claude plugin list
```

The plugin packages MCP configuration, skills and Stata LSP configuration.
The language-server executable must be installed separately for LSP to work.
Native plugin installation does not opt you into `plugins/external`.

For a shared project, use `--scope project` instead of `--scope user`. Choose
either native-plugin setup or regular MCP setup as your starting route to avoid
registering the same Stata server twice. The regular addon installer manages
rules separately and leaves an enabled native `stata-toolbox` responsible for
its LSP. Details are in the [Claude plugin guide](claude-plugin.md).

## Manual client configuration

Use this route for project-specific configuration, an unlisted client, or a
local executable. In an MCP settings screen choose a local/stdio server:

| Field | Value |
|---|---|
| Name | `stata-mcp` |
| Command | `uvx` |
| Arguments | `stata-mcp`, `server` (two separate arguments) |

For clients using the standard `mcpServers` JSON layout, merge this entry into
their existing configuration:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp", "server"]
    }
  }
}
```

Codex uses TOML instead:

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp", "server"]
```

Do not replace other servers or settings with these examples. Paths and schemas
vary; consult your client's configuration UI or the [client guide](clients.md).
Manual registration configures the MCP server only; it does not install addons
or extras. If a desktop client cannot locate `uvx`, provide its absolute path.

## Other ways to obtain the program

### Persistent CLI installation

```bash
uv tool install stata-mcp
stata-mcp --version
stata-mcp install -c codex
```

Or install into your chosen Python environment:

```bash
python -m pip install stata-mcp
stata-mcp --version
```

The automatic client installer currently writes a **uvx-based launch command**,
even when you run it from a pip installation, source checkout or standalone
executable. That automatic setup still requires uv. To use your local program
directly, use manual configuration with its absolute executable path and
`["server"]` as arguments. This also ensures the client uses the Python
environment you intended rather than a separate uvx environment.

### Release executables

Download the matching artifact and its `.sha256` file from
[GitHub Releases](https://github.com/SepineTam/mcp-for-stata/releases):

| Platform | Artifact |
|---|---|
| macOS, Apple Silicon | `stata-mcp-macos-arm64` |
| Linux, x86-64 | `stata-mcp-linux-x86_64` |
| Windows, x86-64 | `stata-mcp-windows-x86_64.exe` |

Check its SHA-256 against the supplied checksum. On macOS/Linux, make the
downloaded file executable, then run it with `--version`. Keep it in a stable
location and use its absolute path as the manual MCP command, with `server` as
the argument. A standalone executable does not bundle Stata or its license.

### Source installation

```bash
git clone https://github.com/SepineTam/mcp-for-stata.git
cd mcp-for-stata
uv sync
uv run stata-mcp --version
```

To make the client run this checkout, register `uv` manually with arguments
`run`, `--directory`, `/absolute/path/to/mcp-for-stata`, `stata-mcp`, `server`.
Running `uv run stata-mcp install` alone still writes the normal uvx launch
configuration; it does not automatically select the checkout as the server.

## Verify the installation

For the recommended route:

```bash
uvx stata-mcp doctor
uvx stata-mcp verify -c codex
```

Replace `codex` with your client where supported by `verify --help`. Doctor
checks the runtime environment; verify inspects configuration, not a live MCP
connection. For a local program use that executable in place of `uvx stata-mcp`.

Restart the client and confirm Stata MCP tools appear. Then ask:

```text
Use MCP-for-Stata to load Stata's auto example dataset and regress price on
mpg and weight. Show me the result and the path to the execution log.
```

This checks the client, MCP server and Stata together. A successful config write
alone is not this final check. Review skipped components separately; older
clients may not support skills, and extra services may need their own setup.

## Update or pin versions

Update the program using the method you installed it with:

```bash
# Refresh a uvx run
uvx --refresh stata-mcp --version

# Update a persistent uv tool
uv tool upgrade stata-mcp

# Update the selected Python environment
python -m pip install --upgrade stata-mcp
```

Replace a standalone executable with the desired release artifact. Update a
source checkout through Git and run `uv sync` again.

Rerun `uvx stata-mcp install -c codex` to check for addon updates, adding
`--with-extra` if you want extras too. Updating the Python program and updating
GitHub components are separate operations. Native Claude plugin updates use
`claude plugin update stata-toolbox@stata-plugin-lib`.

To select a component snapshot, pass `--addon-ref <tag-or-commit>` to `install`.
To pin the running MCP package, use `uvx` as the manual command with arguments
`["--from", "stata-mcp==<version>", "stata-mcp", "server"]`, replacing the
placeholder. Pinning only the installer invocation does not pin the client
configuration it writes.

## Common installation issues

| Symptom | Next step |
|---|---|
| `uvx` or `stata-mcp` is not found | Reopen the terminal after installation, check PATH, or use an absolute executable path |
| Stata is not found | Set `config set cli` to the Stata executable and rerun `doctor --check stata_cli` |
| Tools do not appear | Restart the client and inspect its MCP status; check the launch command and config scope |
| GitHub component download fails | Review the warning and network access, then rerun installation; base MCP may still work |
| An addon is skipped due to local changes | Review your changes; the installer deliberately preserves them |
| Skill or LSP files exist but do not load | Check the client's component support, version and any required language-server executable |
| An extra MCP service fails | Check that service's dependencies and authentication separately |

Continue with [troubleshooting](troubleshooting.md), [configuration](configuration.md)
or the [CLI reference](cli.md) for detailed settings.
