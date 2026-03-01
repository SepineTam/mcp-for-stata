# Stata-MCP Overview

## What is Stata-MCP and Stata?

**Stata-MCP** is a Model Context Protocol (MCP) server that bridges Large Language Models (LLMs) with Stata, enabling autonomous econometric analysis and statistical computation. Built on the FastMCP framework, Stata-MCP exposes Stata's comprehensive analytical capabilities as structured tools that LLMs can invoke programmatically, transforming natural language queries into reproducible Stata workflows.

### Why Stata-MCP?

Stata remains the dominant analytical engine in empirical social science research. In China's economics discipline alone, over 80% of published articles are empirical studies, with more than 98.4% utilizing Stata for analysis. This prevalence stems from Stata's mature ecosystem, methodological completeness, and reliability in reproducing published research.

Stata-MCP addresses a critical gap in AI-assisted research: while modern LLMs excel at code generation and statistical reasoning, they lack native execution environments for domain-specific tools like Stata. By implementing the MCP protocol, Stata-MCP enables:

- **Deterministic Execution**: LLM-generated Stata code executes in a controlled, reproducible environment
- **Methodological Rigor**: Access to Stata's validated econometric implementations ensures analytical integrity
- **Workflow Orchestration**: Complex multi-step analyses (data cleaning → estimation → visualization) become automated pipelines
- **Cross-Platform Compatibility**: Unified abstraction layer across macOS, Windows, and Linux environments

## Architecture Overview

Stata-MCP operates through four architectural layers:

### 1. **Protocol Layer (MCP Server)**
The `FastMCP`-based server (`src/stata_mcp/__init__.py`) implements the Model Context Protocol, exposing Stata operations as structured tools. Each tool defines:
- Input parameter schemas with type validation
- Output serialization for LLM consumption
- Error handling and logging infrastructure
- Resource registration for stateful operations

### 2. **Execution Layer (Stata Integration)**
Platform-specific Stata controllers manage command execution:
- **`StataFinder`**: Locates Stata executables across operating systems (macOS: `/Applications/Stata/`, Windows: `Program Files`, Linux: system PATH)
- **`StataController`**: Manages Stata process lifecycle, command invocation, and exit code monitoring
- **`StataDo`**: Handles do-file execution with log capture and error reporting

### 3. **Security & Monitoring Layer**
Advanced safety features for production deployments:
- **[Security Guard](security.md)**: Validates dofiles against dangerous commands (shell execution, file deletion, etc.)
- **[Monitoring System](monitoring.md)**: Real-time RAM monitoring with automatic process termination
- **Blacklist-based validation**: Blocks dangerous operations before execution
- **Resource limits**: Prevents memory exhaustion and system instability

### 4. **Configuration Layer**
Unified configuration management with hierarchical priority:
- **[Configuration System](configuration.md)**: TOML-based config file at `~/.statamcp/config.toml`
- **Environment variables**: Override settings for specific sessions
- **Priority**: Environment variables > config file > defaults
- **Sections**: DEBUG, SECURITY, PROJECT, MONITOR

### 5. **Application Layer (Modes & Tools)**
Two primary operational modes:

#### **MCP Server Mode** (Default)
Operates as a stdio/HTTP/SSE server, responding to tool invocation requests from MCP-compliant clients. Tools include:

| Tool | Purpose |
|------|---------|
| `stata_do` | Execute do-files with log retrieval |
| `write_dofile` | Create timestamped do-files |
| `append_dofile` | Extend existing do-files immutably |
| `get_data_info` | Analyze CSV/DTA files with statistical summaries |
| `help` | Retrieve Stata command documentation (cached) |
| `ssc_install` | Install packages from SSC/GitHub/net sources |
| `load_figure` | Load Stata-generated graphics for display |
| `read_file` | Generic file reading with encoding support |

#### **Agent Mode** (`agent run` command)
Interactive REPL agent for conversational analysis:
- Read-Eval-Print Loop (REPL) interface for multi-turn sessions
- SQLite-based session management for conversation history
- Custom working directory support via `agent run <path>`
- Environment variables for model configuration (`STATA_MCP_MODEL`, `STATA_MCP_API_KEY`)
- Supports any OpenAI-compatible API endpoint

## Data Processing Pipeline

Stata-MCP implements a polymorphic data analysis system supporting multiple formats:

### **DataInfo Architecture**
Abstract base class `DataInfoBase` with format-specific implementations:
- **`DtaDataInfo`**: Native Stata `.dta` format with metadata extraction
- **`CsvDataInfo`**: CSV files with encoding detection and type inference
- **`ExcelDataInfo`**: Excel workbooks with sheet selection

### **Statistical Metrics**
Configurable metric computation (via `~/.statamcp/config.toml` or environment variables):
- **Default**: observations, mean, standard error, minimum, maximum
- **Extended**: Q1, Q3, skewness, kurtosis, unique value sampling

### **Caching Strategy**
Content-addressable cache using MD5 hashing:
```
~/.statamcp/.cache/data_info__<name>_<ext>__hash_<suffix>.json
```
Cache invalidation occurs automatically on content change detection.

## Project Structure Convention

Stata-MCP enforces a standardized directory layout for reproducible research:

```text
~/Documents/stata-mcp-folder/
├── stata-mcp-log/      # Stata execution logs (timestamped)
├── stata-mcp-dofile/   # Generated do-files (ISO 8601 timestamps)
├── stata-mcp-result/   # Command outputs (outreg2, esttab exports)
└── stata-mcp-tmp/      # Temporary artifacts (data info cache)
```

For AI-assisted research projects, the recommended template (`stata-mcp --init`) creates:

```text
<project_name>/
├── .claude/
│   ├── skills/              # Custom Claude Code skills
│   └── settings.local.json  # MCP server registration
├── source/
│   ├── data/
│   │   ├── raw/             # Immutable source data
│   │   ├── processing/      # Intermediate datasets
│   │   └── final/           # Analysis-ready data
│   ├── figs/                # Publication figures
│   └── tabs/                # Publication tables
├── stata-mcp-folder/        # Stata-MCP working directory
└── CLAUDE.md                # Project-specific instructions
```

## Integration Patterns

### **In AI Clients**
MCP-compliant clients (Claude Code, Cline, Continue) register Stata-MCP as a server in their configuration:

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp"]
    }
  }
}
```

### **In Python Agents**
Stata-MCP agents can be embedded as tools within other agent workflows:

```python
from stata_mcp.agent_as import StataAgent
from agents import Agent, Runner

# Initialize Stata agent and convert to tool
stata_agent = StataAgent()
stata_tool = stata_agent.as_tool

# Embed in a larger agent workflow
research_assistant = Agent(
    name="Research Assistant",
    instructions="You help with economic research using Stata",
    tools=[stata_tool]
)

# Run the agent
result = await Runner.run(
    research_assistant,
    "Analyze the relationship between education and income"
)
```

### **Terminal REPL**
Interactive analysis sessions:

```python
from stata_mcp.agent_as import REPLAgent

agent = REPLAgent(work_dir="~/analysis")
agent.run()  # Starts interactive REPL
```

## Cross-Platform Support

| Platform | Stata Detection | Package Installation | Help System |
|----------|----------------|---------------------|-------------|
| macOS | `/Applications/Stata/StataMP` | Native CLI | ✅ Cached |
| Windows | `Program Files` registry | Do-file delegation | ❌ Not supported |
| Linux | `stata-mp` from PATH | Native CLI | ✅ Cached |

## Design Philosophy

1. **Immutability**: Source files remain unmodified; all operations create timestamped artifacts
2. **Fail-Safety**: Graceful degradation (e.g., `append_dofile` creates new files if source missing)
3. **Reproducibility**: Deterministic paths, automatic logging, and cache invalidation
4. **Extensibility**: Plugin architecture for custom tools and data format handlers
5. **Security First**:
   - **Security Guard**: Blocks dangerous commands before execution
   - **Path Validation**: Restricts file operations to working directory
   - **Resource Monitoring**: Prevents memory exhaustion via RAM monitoring
   - **Sandboxed Execution**: Isolated execution environments for safety

## Advanced Features

### **Security Guard** ✅
Automatically validates all dofile code against dangerous commands:
- Blocks shell execution (`!`, `shell`, `xshell`, etc.)
- Prevents file deletion operations (`erase`, `rm`)
- Stops untrusted code execution (`run`, `do`, `include`)
- Configurable via [Security settings](configuration.md#security-section)

### **RAM Monitoring** ✅
Real-time monitoring of Stata process memory usage:
- Tracks RAM usage during execution
- Automatically terminates processes exceeding limits
- Configurable RAM limits per project
- Minimal overhead with daemon thread architecture
- See [Monitoring documentation](monitoring.md) for details

### **Unified Configuration** ✅
Hierarchical configuration system:
- TOML-based configuration file (`~/.statamcp/config.toml`)
- Environment variable overrides
- Sections: DEBUG, SECURITY, PROJECT, MONITOR
- See [Configuration documentation](configuration.md) for details

### **Sandbox System** (not support now)
Alternative execution backend using Jupyter kernels for environments without Stata licenses or for testing purposes.

### **Multi-Language Support** (not support now)
Configurable language settings for localized error messages and documentation.

## Citation and Acknowledgments

Stata-MCP is developed by the empirical research community to bridge AI assistance with domain-specific analytical tools. Contributions, bug reports, and feature requests are welcome via the [GitHub repository](https://github.com/sepinetam/stata-mcp).

