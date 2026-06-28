<div align="center">
  <a href="https://aidea-labs.com/mcp-for-stata">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="MCP-for-Stata: Integrate Stata into your agent" width="300"/>
  </a>
</div>

# MCP-for-Stata: Integrate Stata into your agent

Enable Claude Code, Codex, OpenClaw, and other AI agents to safely invoke Stata on your local device for data analysis.

> Stata is a registered trademark of StataCorp LLC. This project is an independent community-developed tool and is not affiliated with, endorsed by, or sponsored by StataCorp LLC.

[![en](https://img.shields.io/badge/lang-English-red.svg)](README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](README.zh-CN.md)
[![fr](https://img.shields.io/badge/langue-Français-blue.svg)](README.fr.md)
[![es](https://img.shields.io/badge/idioma-Español-green.svg)](README.es.md)
[![Publish to PyPI](https://github.com/SepineTam/mcp-for-stata/actions/workflows/python-package.yml/badge.svg)](https://github.com/SepineTam/mcp-for-stata/actions/workflows/python-package.yml)
[![PyPI version](https://img.shields.io/pypi/v/stata-mcp.svg)](https://pypi.org/project/stata-mcp/)
[![PyPI Downloads](https://static.pepy.tech/badge/stata-mcp)](https://pepy.tech/projects/stata-mcp)
[![License: AGPL 3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](LICENSE)
[![Issue](https://img.shields.io/badge/Issue-report-green.svg)](https://github.com/sepinetam/mcp-for-stata/issues/new)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SepineTam/mcp-for-stata)

<!-- mcp-name: io.github.SepineTam/mcp-for-stata -->

---
## 🆕 News
- Find more in WeChat: [Why I made it?](https://mp.weixin.qq.com/s/VYkykdDgfPMa5KN0_1BeFQ), and [8 figures find out Stata-MCP](https://mp.weixin.qq.com/s/RKPKA4OWAM5SeZmGtbMRew)
- 🦞 **OpenClaw Support**: Standalone CLI tools for OpenClaw integration (`stata-mcp tool`), see [OpenClaw guide](https://sepinetam.github.io/mcp-for-stata/agents/openclaw.md)
- ✨ **Claude Code Plugin Support**: Official plugin package with MCP server and Stata LSP integration
- Use MCP-for-Stata in Claude Code, see [Claude Code advanced usage](#advanced-claude-code), or in Codex see [Codex advanced usage](#advanced-codex)

> Finding our **newest research**? [View latest research reports](https://aidea-labs.com/mcp-for-stata/reports).

<details>
<summary>Looking for others?</summary>

> **MCP or AI about Stata**
> - A session based MCP server for Stata, [mcp-stata](https://github.com/tmonk/mcp-stata)
> - IDEs (VScode or Cursor) integrated [stata-mcp for VSCode](https://github.com/hanlulong/stata-mcp). Confused them? 💡 [Comparison](#comparison)
> 
> **Datasets and Information**  
> - [STOP Dataset](https://opendata.ai4cssci.com): StataMCP-Team Opendata Project 📊, we have open-sourced a comprehensive dataset collection for social science research, aiming to enable the future of AI-driven and data-powered research paradigms.
</details>

<details>
<summary>Why AGPL 3.0 License?</summary>

The AGPL 3.0 License is a type of open-source license. It does not affect your daily use, and allows you to use, modify, and distribute this software free of charge, provided that you comply with its terms, such as retaining the original copyright notices.

**Notes**: While we strive to make open source accessible to everyone, we regret that we can no longer maintain the Apache-2.0 License. Due to individuals directly copying this project and claiming to be its maintainers, we have decided to change the license to AGPL-3.0 to prevent misuse of the project in ways that go against our original vision.

**Notes**: 尽管我们希望尽可能让所有人都能从开源中获益，但我们很遗憾地宣布无法继续保持 Apache-2.0 License。由于有人直接抄袭本项目并标榜其为项目维护者，我们不得不将 License 更改为 AGPL-3.0，以防止有人滥用本项目进行违背项目初心的事情。

Reason following: 

**Background**: @jackdark425's [repository](https://github.com/jackdark425/aigroup-stata-mcp) directly copied this project and claimed to be the sole maintainer. We welcome open source collaboration based on forks, including but not limited to adding new features, fixing existing bugs, or providing valuable suggestions for the project, but we firmly oppose plagiarism and false attribution.

**Update**: The infringing project has been taken down via GitHub DMCA. [View DMCA takedown details](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md).

**背景**: @jackdark425 的[仓库](https://github.com/jackdark425/aigroup-stata-mcp)直接抄袭了本项目并标榜为项目唯一维护者。我们欢迎基于fork的开源协作，包括但不限于添加新的feature、修改已有bug或对项目提出您宝贵的意见，但坚决反对抄袭和虚假署名行为。

**更新**: 侵权项目已通过GitHub DMCA被takedown，[查看DMCA下架详情](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md)。

</details>

---

## 💡 Quickly Start
### 🚀 One-click installation for all clients!
No config, no manual JSON editing. Just one command installs MCP-for-Stata for **every supported agent** (Claude Code, Codex, OpenClaw, Cursor, Gemini CLI, and more):

```bash
uvx stata-mcp install --all
```

<details>
<summary>Supported Agents 🤖</summary>
Based on our own experience and testing, we recommend using Claude Code, Codex, and OpenClaw.
We have found that Claude and DeepSeek are the two best models across any framework.

| Agent                     | Tag      | Command                           |
|---------------------------|----------|-----------------------------------|
| Claude Desktop            | claude   | uvx stata-mcp install -c claude   |
| Claude Code               | cc       | uvx stata-mcp install -c cc       |
| Gemini CLI                | gemini   | uvx stata-mcp install -c gemini   |
| Cursor                    | cursor   | uvx stata-mcp install -c cursor   |
| Cline (VScode Extension)  | cline    | uvx stata-mcp install -c cline    |
| Codex CLI & Codex Desktop | codex    | uvx stata-mcp install -c codex    |
| OpenCode                  | opencode | uvx stata-mcp install -c opencode |
| OpenClaw                  | openclaw | uvx stata-mcp install -c openclaw |

</details>

If you don't have `uv`, [see the uv installation guide](https://docs.astral.sh/uv/getting-started/installation) to install it. 
Or, use our beta install script (auto-installs `uv` if missing):

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/SepineTam/mcp-for-stata/master/scripts/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/SepineTam/mcp-for-stata/master/scripts/install.ps1 | iex
```

If you don't know how to use them, [download the installation scripts](https://github.com/SepineTam/mcp-for-stata/tree/master/scripts) and double-click it in your device. `install.bat` for Windows users, and `install.command` for macOS users. 

<a name="advanced-claude-code"></a>

### Advanced - Claude Code
As we find Claude Code is the best agent for MCP-for-Stata as its prefect agentic ability, we recommend using it, and there are lots of advanced usage following:

Before using it, please make sure you have ever install `Claude Code`, if you don't know how to install it, visit on [GitHub](https://github.com/anthropics/claude-code)

Generally, you can install MCP-for-Stata globally for one time, you can run:
```bash
claude mcp add stata-mcp --scope user -- uvx stata-mcp
```

Then, you do not need to watch it again. 

<details>
<summary>Local and share with your partners</summary>

If you want to install it locally only for the certain workspace, you can `cd` to your working directory, and run:
```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope local -- uvx --directory $(pwd) stata-mcp
```

It would nothing happen, you can type `claude` and type `/mcp` to find the status. 

Also, collaboration is an essential part of research. You can share your MCP config with your co-authors using:
```bash
claude mcp add stata-mcp --scope project -- uvx stata-mcp
```
In your working directory, you can find a file named `.mcp.json`, your mcp config will be placed here. 

</details>

Then, you can use MCP-for-Stata in Claude Code. Here are some scenarios for using it:

- **Paper Replication**: Replicate empirical studies from economics papers
- **Quick Hypothesis Testing**: Validate economic hypotheses through regression analysis
- **Stata Learning Assistant**: Learn econometrics with step-by-step Stata explanations
- **Code Organization**: Review and optimize existing Stata do-files
- **Result Interpretation**: Understand complex statistical outputs and regression results

If you use Claude Code inside IDEs (either the integrated terminal or the Claude Code Extension), installing our plugin including [MCP-for-Stata](https://github.com/sepinetam/mcp-for-stata) and [Stata LSP](https://github.com/euglevi/stata-language-server) maintained by @euglevi. 

```bash
# Add the MCP-for-Stata marketplace
claude plugin marketplace add SepineTam/mcp-for-stata

# Install the plugin to local, project or user scope
claude plugin install stata-toolbox -s project
```

> The language server gives AI-generated Stata code better syntax awareness and completion, which improves output quality. We package the LSP in compliance with its license and give full attribution to the original author.

<a name="advanced-codex"></a>

### Advanced - Codex
We find that many researchers are using Codex as their agent, therefore we also provide instructions for Codex users. 

I figure that researchers are not using Codex CLI but Codex Desktop, so we can say it is easier to config MCP-for-Stata than other agents. 

You just need to say `Install MCP-for-Stata for yourself globally from https://www.statamcp.com or visit https://github.com/SepineTam/mcp-for-stata` then restart your Codex Desktop after it say ready. 

Also, if you want to install it manually, here are two ways:

#### A. Install in Codex Desktop GUI
1. Open your Codex Desktop APP
2. Click `Settings` in the bottom-left corner
3. Find `MCP servers` on the left side
4. Click `Add server`
5. Fill with the following:
    ```
    Name: stata-mcp
    Command to launch: uvx
    Arguments: stata-mcp
    ```
6. Click `Save`
7. Then, restart your Codex Desktop and enjoy it. 

#### B. Install with Codex CLI
For CLI mode, just run the following command in your terminal
```bash
uvx stata-mcp install -c codex
```

Or use
```bash
codex mcp add stata-mcp -- uvx stata-mcp
```

### Other Clients
> Standard config requires: please make sure the stata is installed at the default path, and the stata cli (for macOS and Linux) exists.

The standard config json as follows, you can DIY your config via add envs.
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

For more detailed usage information, visit the [Usage guide](https://sepinetam.github.io/mcp-for-stata/usage).

### Prerequisites
- [uv](https://github.com/astral-sh/uv) - Package installer and virtual environment manager
- Claude Code, Codex, OpenClaw or other Agents
- Stata License
- Your API-KEY from LLM

If you want to check whether your device is supported, you can run:
```bash
uvx stata-mcp doctor
```

It displays basic information about your device and checks whether your setup is supported.

<details>
<summary>Example output</summary>

```
stata-mcp v1.17.0 — Doctor Report

  [PASS] os: macOS (Darwin 25.3.0, arm64)
  [PASS] python: 3.13.5
  [PASS] uv: uv 0.11.13
  [PASS] dependencies: all required packages available
  [PASS] stata_cli: /usr/local/bin/stata-mp (from env)
  [PASS] stata_execution: OK (0.1s)
  [PASS] config: /Users/sepinetam/.statamcp/config.toml (loaded)
  [PASS] working_dir: /Users/sepinetam/Documents/Github/stata-mcp (writable)
  [PASS] guard: enabled, loaded 27 rules
  [PASS] monitor: disabled (psutil available)
  [PASS] pypi: reachable (4.86s)
  [PASS] cleanup: 0 old files (0 B) found; cleanup disabled (CLEAN_LOG_DAYS=-1)

Summary: 12 passed, 0 failed, 0 warning(s), 0 skipped
```

</details>

> Notes:
> 1. If you are located in China and package downloads are slow, see the [solution](docs/troubleshooting.md#package-download-is-slow-or-fails).
> 2. Claude is the best choice for MCP-for-Stata, for Chinese, I recommend to use DeepSeek as your model provider as it is cheap and powerful, also the score is highest in China provider, if you are increased in it, visit the report [How to use StataMCP improve your social science research](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research).

## Comparison

There are several Stata-related MCP projects. The table below was generated by Claude Code after analyzing each codebase directly.

| Feature | [MCP-for-Stata](https://aidea-labs.com/mcp-for-stata) (this) | [haoyu-haoyu/stata-ai-fusion](https://github.com/haoyu-haoyu/stata-ai-fusion) | [hanlulong/stata-mcp](https://github.com/hanlulong/stata-mcp) | [tmonk/mcp-stata](https://github.com/tmonk/mcp-stata) |
|---|---|---|---|---|
| **Best for** | Agent-driven analysis (Claude Code, Codex, OpenClaw) | Interactive sessions, graph export, and curated Stata knowledge | Users who write and run Stata code inside VSCode themselves | Research workflows (replication, robustness, publication QA) |
| **Agents** | All | All | VSCode window must stay active | All |
| **Type** | MCP Server + CLI toolkit | MCP Server + Skill KB + VS Code Extension | VSCode Extension (localhost server, not standalone MCP) | Session-based MCP Server |
| **Execution** | do-file via subprocess | pexpect interactive session + batch fallback | IDE-embedded runner via localhost :4000 | pystata (Stata 17+) |
| **Safety** | Command guard + RAM monitor | Cancel command + session cleanup | — | — |
| **Data analysis** | CSV, DTA, XLSX, SPSS handlers | In-session `inspect_data` / `codebook` | — | In-session `describe` / `codebook` |
| **Logs** | Text + SMCL readers | In-session `search_log` | — | Built-in log reader |
| **Graphs** | — | Auto-detect + `export_graph` PNG/SVG/PDF | — | Export, cache, SVG/PNG |
| **CLI Support** | Native (same tools as MCP server) | Basic entry point | — | — |
| **Sessions** | — | Multi named sessions with idle timeout | — | Multi-session, background tasks |
| **IDE plug-in** | — | Native VS Code / Cursor extension | Native VSCode / Cursor | Stata Workbench (VS Code) |
| **Skill / Knowledge** | Tool-focused skill for MCP-for-Stata (742 lines) | 5,653-line general Stata skill knowledge base | — | 20+ specialized research skills (causal inference, replication, publication QA, etc.) |
| **Install** | `uvx stata-mcp install` | `uvx --from stata-ai-fusion stata-ai-fusion` | VS Code Marketplace | `uvx` or install script |

## 📝 Documentation
> MCP-for-Stata documents visit https://sepinetam.github.io/mcp-for-stata

### Core Documentation
- **[Complete Documentation](https://sepinetam.github.io/mcp-for-stata/)**: Full documentation site with all features
- **[Configuration Guide](https://sepinetam.github.io/mcp-for-stata/configuration)**: Unified TOML-based configuration system
- **[Security Guard](https://sepinetam.github.io/mcp-for-stata/security)**: Security validation for dangerous commands
- **[Monitoring System](https://sepinetam.github.io/mcp-for-stata/monitoring)**: RAM monitoring and resource limits
- **[Architecture Overview](https://sepinetam.github.io/mcp-for-stata/overview)**: System design and integration patterns

### Key Features
- **[Security Guard](https://sepinetam.github.io/mcp-for-stata/security)**: Blocks dangerous commands (`!`, `shell`, `erase`, etc.)
- **[RAM Monitoring](https://sepinetam.github.io/mcp-for-stata/monitoring)**: Prevents memory exhaustion with configurable limits
- **[Unified Configuration](https://sepinetam.github.io/mcp-for-stata/configuration)**: TOML config + environment variables
- Cross-platform support (macOS, Windows, Linux)
- Automatic log capture and error reporting

## 🐛 Report Issues
If you encounter any bugs or have feature requests, please [open an issue](https://github.com/sepinetam/mcp-for-stata/issues/new).

## 📄 License
[GNU Affero General Public License v3.0](LICENSE)

## 📚 Citation
If you use MCP-for-Stata in your research, and it really helps you, you can cite this repository using one of the following formats:

### BibTeX
```bibtex
@software{sepinetam2025stata,
  author = {Song Tan},
  title = {MCP-for-Stata: Integrate Stata into your agent},
  year = {2025},
  url = {https://github.com/sepinetam/mcp-for-stata},
  version = {1.20.0}
}
```

### APA
```
Song Tan. (2025). MCP-for-Stata: Integrate Stata into your agent (Version 1.20.0) [Computer software]. https://github.com/sepinetam/mcp-for-stata
```

### Chicago
```
Song Tan. 2025. "MCP-for-Stata: Integrate Stata into your agent." Version 1.20.0. https://github.com/sepinetam/mcp-for-stata.
```

## 📬 Contact
Email: [sepinetam@gmail.com](mailto:sepinetam@gmail.com)

Or contribute directly by submitting a [Pull Request](https://github.com/sepinetam/mcp-for-stata/pulls)! We welcome contributions of all kinds, from bug fixes to new features.

## 📃 Statement
Stata is a registered trademark of [StataCorp LLC](https://www.stata.com/company/). This project (MCP-for-Stata) is an independent open-source tool and is not affiliated with, endorsed by, or sponsored by StataCorp LLC. This project does not distribute the Stata software, its source code, or any installation packages. Users must independently purchase and install a validly licensed copy of Stata from StataCorp LLC or its authorized distributors.

This project is licensed under [AGPL-3.0](LICENSE). The project maintainers accept no liability for any loss or damage arising solely from the use of this project's code or documentation.

More information: refer to the Chinese version at [README.zh-CN.md](README.zh-CN.md); in case of any conflict, the Chinese version shall prevail.

## ✨ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)
