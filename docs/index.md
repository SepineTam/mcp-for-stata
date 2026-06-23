# MCP-for-Stata

**Integrate Stata into your agent.**

## 🆕 MCP-for-Stata Now Supports OpenClaw

**MCP-for-Stata now supports OpenClaw!** MCP-for-Stata provides standalone CLI tools, paste the following command to your openclaw, it would install the skill automatically.

```text
Install `stata-skill` from ClawHub by @SepineTam. 
```

See [OpenClaw Integration Guide](agents/openclaw.md) for complete documentation.

## Quickly Start

> Requirements: [uv](https://docs.astral.sh/uv/getting-started/installation/) or python 3.11+  
> If you don't have `uv` but `python`, you can install it with `pip install uv`.  

First, you should check whether your device is supported by stata-mcp.  
```bash
uvx stata-mcp doctor
```
If each check is passed, you can start using stata-mcp.  
If remind not found STATA_CLI, you can see [StataFinder](core/stata/finder.md#not-found) to solve it.

The common configuration file (json)
```json
{
  "mcpServers":{
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

### Use MCP-for-Stata in Claude Code

We recommend using MCP-for-Stata with [Claude Code](https://github.com/anthropics/claude-code) for its excellent agentic capabilities.

Before using it, please make sure you have Claude Code installed. If you don't know how to install it, visit [GitHub](https://github.com/anthropics/claude-code).

Open your terminal, `cd` to your working directory, and run:

```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp
```

This will create a `.mcp.json` file in your working directory with the MCP configuration.

#### Use Cases

- **Paper Replication**: Replicate empirical studies from economics papers
- **Quick Hypothesis Testing**: Validate economic hypotheses through regression analysis
- **Stata Learning Assistant**: Learn econometrics with step-by-step Stata explanations
- **Code Organization**: Review and optimize existing Stata do-files
- **Result Interpretation**: Understand complex statistical outputs and regression results

For detailed usage guide, visit [agents/claude_code.md](agents/claude_code.md).

---

If you want to explore more [clients](clients.md) or [agents](agents/index.md), visit their respective documentation.

## Documentation

### Core Documentation

- **[Overview](overview.md)**: Architecture, design philosophy, and integration patterns
- **[Usage](usage.md)**: Common usage patterns and examples
- **[Configuration](configuration.md)**: Complete configuration guide with all options
- **[Clients](clients.md)**: Supported MCP clients and setup instructions
- **[Claude Plugin](claude-plugin.md)**: Official Claude Code plugin integration guide

### Advanced Features

- **[Docker](docker.md)**: Run MCP-for-Stata in containerized environments
- **[Security Guard](security.md)**: Security validation system for dangerous commands
- **[Monitoring System](monitoring.md)**: RAM monitoring and resource limits

### Core Components

- **[Stata Integration](core/stata/)**
  - [StataDo](core/stata/do.md): Do-file execution
  - [StataFinder](core/stata/finder.md): Stata executable detection
  - [Stata Help](core/stata/help.md): Command documentation
  - [Package Installation](core/stata/package.md): SSC and GitHub packages

- **[MCP Tools](mcp/tools.md)**: Available MCP tools and usage
- **[MCP Resources](mcp/resources.md)**: MCP resources and capabilities

### Agents

- **[Agent Index](agents/index.md)**: Overview of agent modes
- **[Claude Code Integration](agents/claude_code.md)**: Detailed Claude Code setup

## Quick Links

### For Users

- [Getting Started](#quickly-start)
- [Configuration Guide](configuration.md)
- [Security Documentation](security.md)
- [Monitoring Setup](monitoring.md)

### For Developers

- [Architecture Overview](overview.md)
- [MCP Tools Reference](mcp/tools.md)
- [Core Components](core/stata/)

### Configuration

- [Basic Configuration](configuration.md#configuration-file)
- [Security Settings](configuration.md#security-section)
- [Monitoring Settings](configuration.md#monitor-section)
- [Environment Variables](configuration.md#environment-variables)

