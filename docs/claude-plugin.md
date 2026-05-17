# Claude Plugin Integration

## Overview

Stata-MCP provides official native plugin support for Claude Code, integrating two powerful components in `stata-toolbox@stata-plugin-lib` now:

1. **Stata-MCP Server**: Model Context Protocol server for Stata execution
2. **Stata LSP (Language Server Protocol)**: Advanced language support for Stata do-files

This plugin package, named **stata-toolbox**, delivers a unified development environment for empirical research, combining the analytical power of Stata with AI assistance and advanced IDE features.

## What is Claude Plugin?

Claude Plugin is a plugin system introduced in Claude Code that allows developers to package and distribute:

- **MCP Servers**: Model Context Protocol servers that expose tools to Claude
- **LSP Servers**: Language Server Protocol servers for enhanced editor support
- **Skills**: Skills for expand Claude agent abilities
- **Configuration**: Pre-configured settings for optimal integration

The plugin system enables one-command installation of complex development environments, replacing manual configuration with reproducible, version-controlled packages.

## Plugin Structure

> More plugin config schema could be found in [plugins-reference](https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema) from Claude. 

```
.claude-plugin/
├── marketplace.json          # Plugin registry manifest
└── plugins/
    └── stata-toolbox/       # Plugin package
        └── plugin.json        # Plugin configuration
```

### Marketplace Manifest (`marketplace.json`)

```json
{
  "name": "stata-plugin-lib",
  "owner": {
    "name": "Song Tan",
    "email": "sepinetam@gmail.com"
  },
  "plugins": [
    {
      "name": "stata-toolbox",
      "source": "./plugins/stata-toolbox",
      "description": "The official working package of Stata-MCP plugin, including mcp config and stata lsp."
    }
  ]
}
```

**Fields:**
- `name` (string): Marketplace library identifier (kebab-case, no spaces)
- `owner` (object): Author information
  - `name` (string): Author name
  - `email` (string): Contact email
- `plugins` (array): List of plugin packages
  - `name` (string): Plugin identifier
  - `source` (string): Relative path to plugin directory
  - `description` (string): Plugin functionality summary

### Plugin Configuration (`plugin.json`)

```json
{
  "name": "stata-toolbox",
  "version": "0.1.0",
  "description": "The official working package of Stata-MCP plugin, including mcp config and stata lsp.",
  "author": {
    "name": "Song Tan",
    "email": "sepinetam@gmail.com",
    "url": "https://www.sepinetam.com"
  },
  "homepage": "https://statamcp.com",
  "repository": "https://github.com/sepinetam/stata-mcp",
  "license": "AGPL-3.0",
  "keywords": ["stata", "econometrics", "empirical analysis"],
  "mcpServers": {
    ...
  },
  "lspServers": {
    ...
  }
}
```

**Configuration Sections:**

#### MCP Servers Configuration

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx", 
      "args": [
        "stata-mcp"
      ]
    }
  }
}
```

**command**: The command to execute the MCP server. Using `uvx` allows running installed Python packages directly without activating a virtual environment.

**args**: Array of command-line arguments passed to the command. `["stata-mcp"]` specifies the package name to run.

#### LSP Servers Configuration

```json
"lspServers": {
  "stata": {
    "command": "stata-language-server",
    "args": [],
    "extensionToLanguage": {
      ".do": "stata"
    },
    "settings": {
      "stata": {
        "setMaxLineLength": 120,
        "setIndentSpace": 4,
        "enableCompletion": true,
        "enableDocstring": true,
        "enableStyleChecking": true,
        "enableFormatting": true
      }
    }
  }
}
```

> **Notes**: You should install `stata-language-server` first via `pipx install "git+https://github.com/euglevi/stata-language-server.git"`. 

**command**: The LSP server binary executable. Must be available in the system PATH.

**args**: Array of command-line arguments passed to the LSP server. Empty array means no additional arguments.

**extensionToLanguage**: Maps file extensions to language identifiers. `.do` files are mapped to the `stata` language for proper LSP support.

**settings**: LSP-specific configuration object. The `stata` key contains Stata language server settings for code completion, formatting, and style checking.

## Installation

### Prerequisites

Before installing the plugin, ensure following requirements are met:

1. **Claude Code**: Install via official installer
   ```bash
   # macOS/Linux
   curl -fsSL https://claude.ai/install.sh | bash

   # Windows
   irm https://claude.ai/install.ps1 | iex
   ```

2. **Stata**: Valid Stata 17+ license with Stata MP installed

3. **Python Package**: `stata-mcp` package available
   ```bash
   # Verify installation
   uvx stata-mcp doctor
   ```

4. **Stata LSP**: Language server installed
   ```bash
   pipx install "git+https://github.com/euglevi/stata-language-server.git"
   ```

5. **uv**: Package runner (recommended)
   ```bash
   # Install via homebrew
   brew install uv

   # Or via official installer
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### Installation Method

Add the marketplace registry and install the plugin:

```bash
# Add marketplace
claude plugin marketplace add sepinetam/stata-mcp

# Install plugin to user scope (default)
claude plugin install stata-toolbox

# Install to project scope (shared with team)
claude plugin install stata-toolbox --scope project

# Install to local scope (gitignored)
claude plugin install stata-toolbox --scope local
```

The plugin automatically uses the current directory as the working directory for Stata operations.

### Verification

After installation, verify the plugin is loaded:

```bash
# List installed plugins
claude plugin list
```

### How It Works

Once installed, the plugin provides seamless integration:

**1. Automatic Loading**
Claude Code automatically detects:
- `.claude-plugin/marketplace.json` → Plugin registry
- `plugins/stata-toolbox/plugin.json` → Plugin configuration

**2. MCP Tools**
The Stata-MCP server exposes tools that Claude can invoke:
- `stata_do`: Execute Stata code
- `write_dofile`: Create do-files
- `get_data_info`: Analyze datasets
- `help`: Get Stata command documentation
- And more...

**3. LSP Features**
The Stata LSP provides advanced editor support:
- **Syntax Highlighting**: Enhanced .do file coloring
- **Completion**: Auto-suggest Stata commands
- **Hover Documentation**: Mouse over commands for help
- **Error Detection**: Real-time syntax validation
- **Formatting**: Auto-format .do files

### Example Workflows

> This part is generated by AI, please review before use. If you want to achieve the best results, you should edit your `~/.claude/CLAUDE.md` with your own preferences. 

#### Paper Replication

```markdown
> Load the dataset from "source/data/CPS_2018.dta"
> Replicate Table 3 from Mincer (1974) using OLS regression
> Export the regression table to LaTeX format

Claude:
1. Uses get_data_info to understand dataset structure
2. Creates do-file with write_dofile
3. Executes with stata_do
4. Exports table to stata-mcp-result/
```

#### Quick Hypothesis Testing

```markdown
> Test whether education returns have increased post-2008 financial crisis
> Use difference-in-differences with college enrollment as treatment

Claude:
1. Generates DiD specification
2. Runs stata_do with event study design
3. Presents results with economic interpretation
```

## Comparison: Plugin vs Manual Configuration

### Manual Configuration

Traditional approach with command:
```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

or requires manual `.mcp.json` editing:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"],
      "env": {
        "STATA_MCP__CWD": "/absolute/path/to/project"
      }
    }
  }
}
```

### Plugin-Based Configuration

**With Plugin:**

```bash
# Single command installation
claude plugin marketplace add sepinetam/stata-mcp
claude plugin install stata-toolbox
```

### Comparison

| Feature          | Manual Configuration                 | Plugin Installation                      |
|------------------|--------------------------------------|------------------------------------------|
| **Setup**        | Edit `.mcp.json` manually or command | One-command installation                 |
| **MCP Server**   | ✅                                    | ✅                                        |
| **LSP Server**   | ❌ Separate installation              | ✅ Included                               |
| **Team Sharing** | ✅                                    | ✅                                        |
| **Updates**      | Auto update the latest MCP           | Auto update MCP and manual update others |

## Architecture

### Plugin Loading Process

```
1. Claude Code Startup
   ↓
2. Scan for .claude-plugin/marketplace.json
   ↓
3. Parse plugin registry
   ↓
4. Load each plugin's plugin.json
   ↓
5. Register MCP servers
   ↓
6. Initialize LSP servers
   ↓
7. Apply plugin configurations
   ↓
8. Plugin ready for use
```

### Component Interaction

```
┌─────────────────────────────────────────────────────┐
│                   Claude Code                       │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────┴────────────┐
         │                          │
    ┌────▼─────┐                ┌────▼─────┐
    │   MCP    │                │   LSP    │
    │  Server  │                │  Server  │
    └────┬─────┘                └────┬─────┘
         │                           │
    ┌────▼───────────────────────────▼────┐
    │         Stata-MCP Package           │
    │  - stata_do tool                    │
    │  - Data analysis tools              │
    │  - Help system                      │
    └─────────────────────────────────────┘
         │
    ┌────▼──────────┐
    │     Stata     │
    │  Executable   │
    └───────────────┘
```

## Troubleshooting

### Plugin Not Detected

**Symptom:** Plugin installed but Claude Code doesn't show tools

**Solutions:**
1. Restart Claude Code completely
2. Verify JSON syntax in marketplace.json and plugin.json
3. Check file permissions (must be readable)
4. Ensure plugin is installed correctly
5. Run `claude plugin list` to verify

### MCP Server Connection Failed

**Symptom:** Tools show error "Failed to connect to MCP server"

**Diagnosis:**
```bash
# Test MCP server independently
uvx stata-mcp doctor

# Check if Stata is accessible
stata-se --version

# Verify uvx installation
uvx --version
```

**Solutions:**
1. Install missing dependencies:
   ```bash
   pip install stata-mcp
   ```

2. Verify Stata installation path

3. Check environment variables are correctly set

### LSP Not Working

**Symptom:** No syntax highlighting or completion in .do files

**Diagnosis:**
```bash
# Check if stata-language-server is installed
which stata-language-server

# Test LSP server
stata-language-server --help
```

**Solutions:**
1. Install stata-language-server:
   ```bash
   npm install -g stata-language-server
   ```

2. Verify file extension mapping:
   ```json
   {
     "extensionToLanguage": {
       ".do": "stata"
     }
   }
   ```

3. Check LSP logs in Claude Code

## Best Practices

1. **Verify Installation**: Check system compatibility with `uvx stata-mcp doctor` before installing
2. **Environment Variables**: Use `.env` file or project settings for sensitive data
3. **Documentation**: Maintain project-specific CLAUDE.md with research instructions
4. **Version Updates**: Keep plugin updated for latest features and bug fixes

## Related Documentation

- [Configuration Guide](configuration.md) - Advanced configuration options
- [Security Documentation](security.md) - Security guard system
- [Monitoring Guide](monitoring.md) - Resource monitoring
- [MCP Tools Reference](mcp/tools.md) - Available tools
- [Usage Examples](usage.md) - Common workflows
- [Client Configuration](clients.md) - Alternative client setups

## License and Attribution

stata-toolbox plugin is part of the Stata-MCP project.

- **License**: AGPL-3.0
- **Copyright**: (c) 2026 Song Tan (Sepine Tam), Inc.
- **Authors**: Song Tan (sepinetam@gmail.com)

**Stata LSP**: Copyright by [euglevi](https://github.com/euglevi/stata-language-server) with [MIT License](https://github.com/euglevi/stata-language-server/blob/main/LICENSE)

The plugin integrates independently developed components:
- **Stata-MCP Server**: [GitHub Repository](https://github.com/sepinetam/stata-mcp)
- **Stata LSP**: [GitHub Repository](https://github.com/euglevi/stata-language-server)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-02-12
**Maintainer**: Song Tan (sepinetam@gmail.com)
