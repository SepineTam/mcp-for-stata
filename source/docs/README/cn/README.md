<h1 align="center">
  <a href="https://www.statamcp.com">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="logo" width="300"/>
  </a>
</h1>

<h1 align="center">Stata-MCP</h1>

<p align="center"> 
    让大语言模型（LLM）帮助您使用Stata完成回归分析 ✨<br>
    让 reg monkey 进化为 causal thinker 🐒 -> 🧐
</p>

[![en](https://img.shields.io/badge/lang-English-red.svg)](../../../../README.md)
[![cn](https://img.shields.io/badge/语言-中文-yellow.svg)](README.md)
[![fr](https://img.shields.io/badge/langue-Français-blue.svg)](../fr/README.md)
[![sp](https://img.shields.io/badge/Idioma-Español-green.svg)](../sp/README.md)
[![PyPI version](https://img.shields.io/pypi/v/stata-mcp.svg)](https://pypi.org/project/stata-mcp/)
[![PyPI Downloads](https://static.pepy.tech/badge/stata-mcp)](https://pepy.tech/projects/stata-mcp)
[![License: AGPL 3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](../../../../LICENSE)
[![Issue](https://img.shields.io/badge/Issue-report-green.svg)](https://github.com/sepinetam/stata-mcp/issues/new)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/SepineTam/stata-mcp)

---
**Notes**：尽管我们希望尽可能让所有人都能从开源中获益，但我们很遗憾地宣布无法继续保持 Apache-2.0 License。由于有人直接抄袭本项目并标榜其为项目维护者，我们不得不将 License 更改为 AGPL-3.0，以防止有人滥用本项目进行违背项目初心的事情。

**背景**：@jackdark425 的[仓库](https://github.com/jackdark425/aigroup-stata-mcp)直接抄袭了本项目并标榜为项目唯一维护者。我们欢迎基于fork的开源协作，包括但不限于添加新的feature、修改已有bug或对项目提出您宝贵的意见，但坚决反对抄袭和虚假署名行为。

**更新**: 侵权项目已通过GitHub DMCA被takedown，点击[这里](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md)查看详情。

---
**新闻**：
- 在微信公众号中阅读更多：[为什么做Stata-MCP？](https://mp.weixin.qq.com/s/VYkykdDgfPMa5KN0_1BeFQ)，和 [8张图带你了解 Stata-MCP](https://mp.weixin.qq.com/s/RKPKA4OWAM5SeZmGtbMRew)
- 🦞 **OpenClaw 支持**：独立 CLI 工具用于 OpenClaw 集成（`stata-mcp tool`），详见 [OpenClaw 指南](https://docs.statamcp.com/agents/openclaw.md)
- ✨ **Claude Code 插件支持**：官方插件包，集成 MCP 服务器和 Stata LSP
- 在Claude Code中使用Stata-MCP，请查看[此处](#高级---claude-code)

> 寻找我们的**最新研究**？点击[此处](../../../reports/README.md)或访问[报告网站](https://www.statamcp.com/reports)。

<details>
<summary>正在寻找其他？</summary>

> - [STOP](https://opendata.ai4cssci.com)：StataMCP-Team 开放数据项目 📊，我们开源了全面的数据集集合用于社会科学研究，旨在实现 AI 驱动和数据赋能的研究范式未来。
> - [追踪 DID](https://github.com/asjadnaqvi/DiD)：如果您想获取关于DID（双重差分法）的最新信息，请点击[此处](https://asjadnaqvi.github.io/DiD/)。现在有[Sepine Tam](https://github.com/sepine)和[StataMCP-Team](https://github.com/statamcp-team)的中文翻译 🎉
> - Jupyter Lab 使用方法（重要提示：Stata 17+）[此处](../../JupyterStata.md)
> - [NBER-MCP](https://github.com/sepinetam/NBER-MCP) & [AER-MCP](https://github.com/sepinetam/AER-MCP) 🔧 建造之下
> - [Econometrics-Agent](https://github.com/FromCSUZhou/Econometrics-Agent)
> - [TexIV](https://github.com/sepinetam/TexIV)：一个基于机器学习的框架，利用先进的NLP和机器学习技术将文本数据转化为可用于实证研究的变量
> - VScode 或 Cursor 集成 [此处](https://github.com/hanlulong/stata-mcp)。搞不清楚？️💡 [区别](../../Difference.md)

</details>

## 💡 快速开始
### 为所有Agent安装
如果您不想经历复杂的设置，只需运行以下命令：
```bash
uvx stata-mcp install --all
```

<details>
<summary>支持的 Agents 🤖</summary>
根据我们自身的经验和测试，我们推荐使用 Claude Code、Codex 和 OpenClaw。
我们发现 Claude 和 DeepSeek 是在任何框架下表现最好的两个模型。

| Agent                     | 标签     | 命令                               |
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

如果您没有 `uv`，请访问[此处](https://docs.astral.sh/uv/getting-started/installation)安装。
或者，使用我们的 beta 安装脚本（如果缺少 uv 会自动安装）：

**macOS / Linux：**
```bash
curl -fsSL https://raw.githubusercontent.com/SepineTam/stata-mcp/master/scripts/install.sh | bash
```

**Windows (PowerShell)：**
```powershell
irm https://raw.githubusercontent.com/SepineTam/stata-mcp/master/scripts/install.ps1 | iex
```

如果你不知道如何去使用命令行进行安装，尝试点击[这里](https://github.com/SepineTam/stata-mcp/tree/master/scripts)，并且下载安装脚本，并在本地双击运行。`install.bat` 为了 Windows 用户，并且 `install.command` for macOS 用户。

如果因为网络问题出现失败，参考[使用镜像网站](../../ChinaUsers/uv.md)

### 高级 - Claude Code
由于我们发现 Claude Code 凭借其出色的 agentic 能力是 Stata-MCP 的最佳选择，我们推荐使用它，以下是大量高级用法：

在使用之前，请确保您已安装 `Claude Code`，如果您不知道如何安装，请访问 [GitHub](https://github.com/anthropics/claude-code)

一般来说，您可以全局安装 Stata-MCP 一次，运行：
```bash
claude mcp add stata-mcp --scope user -- uvx stata-mcp
```

然后，您就不需要再关注它了。

<details>
<summary>为项目私有安装或与您的合作者共享</summary>

如果您只想为特定工作区本地安装，可以 `cd` 到您的工作目录，然后运行：
```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope local -- uvx --directory $(pwd) stata-mcp
```

这不会发生什么，您可以输入 `claude` 并键入 `/mcp` 来查看状态。

此外，协作是研究的重要组成部分。您可以使用以下命令与您的合作者共享 MCP 配置：
```bash
claude mcp add stata-mcp --scope project -- uvx stata-mcp
```

在您的工作目录中，您可以找到一个名为 `.mcp.json` 的文件，您的 mcp 配置将放在这里。

</details>

然后，您就可以在 Claude Code 中使用 Stata-MCP。以下是一些使用场景：

- **论文复刻**：复刻经济学论文中的实证研究
- **快速假设检验**：通过回归分析验证经济学假设
- **Stata 学习助手**：通过逐步 Stata 解释学习计量经济学
- **代码整理**：审查和优化现有 Stata do-files
- **结果解释**：理解复杂的统计输出和回归结果

如果您在 IDE 中使用 Claude Code（无论是集成终端还是 Claude Code Extension），请安装我们的插件，包括 [Stata-MCP](https://github.com/sepinetam/stata-mcp) 和 [Stata LSP](https://github.com/euglevi/stata-language-server) 由 @euglevi 维护。

```bash
# 添加 Stata-MCP 市场
claude plugin marketplace add SepineTam/stata-mcp

# 将插件安装到 local、project 或 user 范围
claude plugin install stata-toolbox -s project
```

> 语言服务器为 AI 生成的 Stata 代码提供更好的语法感知和补全功能，从而提高输出质量。我们在遵守其许可证的前提下打包 LSP，并给予原作者完整的署名。

### 其他客户端
> 标准配置要求：请确保 Stata 安装在默认路径，并且在 macOS 和 Linux 上存在 Stata CLI。

标准配置 json 如下，您可以通过添加环境变量来自定义配置。
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

有关更详细的使用信息，请访问[使用指南](https://docs.statamcp.com/usage)。

### 前提条件
- [uv](https://github.com/astral-sh/uv) - 包安装器和虚拟环境管理器
- Claude Code、Codex、OpenClaw 或其他 Agents
- Stata 许可证
- 您的 LLM API-KEY

如果您想检查您的设备是否受支持，可以运行：
```bash
uvx stata-mcp doctor
```

它会显示有关您设备的基本信息，并检查您的设置是否受支持。

<details>
<summary>示例输出</summary>

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

> 注：
> 1. 如果您位于中国，可以在此处找到简短的 uv 使用文档[此处](../../ChinaUsers/uv.md)。
> 2. Claude 是 Stata-MCP 的最佳选择，对于中文用户，我推荐使用 DeepSeek 作为您的模型提供商，因为它价格便宜且功能强大，在中国提供商中得分最高，如果您对此感兴趣，请访问报告[How to use StataMCP improve your social science research](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research)。

## 对比

目前有几个与 Stata 相关的 MCP 项目。下表由 Claude Code 在直接分析每个代码库后生成。

| 功能 | Stata-MCP (本项目) | hanlulong/stata-mcp | tmonk/mcp-stata |
|---|---|---|---|
| **Agents** | 全部 | VSCode 窗口必须保持活动 | 全部 |
| **类型** | MCP 服务器 + CLI 工具包 | VSCode 扩展（本地服务器，非独立 MCP） | 基于会话的 MCP 服务器 |
| **执行** | 通过子进程执行 do-file | 通过 localhost :4000 的 IDE 嵌入式运行器 | pystata (Stata 17+) |
| **安全性** | 命令守卫 + RAM 监控 | — | — |
| **数据分析** | CSV、DTA、XLSX、SPSS 处理程序 | — | 会话内 `describe` / `codebook` |
| **日志** | 文本 + SMCL 阅读器 | — | 内置日志阅读器 |
| **图表** | — | — | 导出、缓存、SVG/PNG |
| **CLI 支持** | 原生（与 MCP 服务器相同的工具） | — | — |
| **会话** | — | — | 多会话、后台任务 |
| **IDE 插件** | — | 原生 VSCode / Cursor | Stata Workbench (VS Code) |
| **安装** | `uvx stata-mcp install` | VS Code 市场 | `uvx` 或安装脚本 |
| **最佳适用** | Agent 驱动分析（Claude Code、Codex、OpenClaw） | 自己在 VSCode 中编写和运行 Stata 代码的用户 | 研究工作流（复刻、稳健性、发表 QA） |

## 📝 文档
> Stata-MCP 文档请访问 https://docs.statamcp.com

### 核心文档
- **[完整文档](https://docs.statamcp.com/)**：包含所有功能的完整文档站点
- **[配置指南](https://docs.statamcp.com/configuration)**：基于 TOML 的统一配置系统
- **[Security Guard](https://docs.statamcp.com/security)**：危险命令的安全验证
- **[监控系统](https://docs.statamcp.com/monitoring)**：RAM 监控和资源限制
- **[架构概览](https://docs.statamcp.com/overview)**：系统设计和集成模式

### 核心功能
- **[Security Guard](https://docs.statamcp.com/security)**：阻止危险命令（`!`、`shell`、`erase` 等）
- **[RAM 监控](https://docs.statamcp.com/monitoring)**：通过可配置限制防止内存耗尽
- **[统一配置](https://docs.statamcp.com/configuration)**：TOML 配置 + 环境变量
- 跨平台支持（macOS、Windows、Linux）
- 自动日志捕获和错误报告

## 🐛 报告问题
如果您遇到任何错误或有功能请求，请[提交问题](https://github.com/sepinetam/stata-mcp/issues/new)。

## 📄 许可证
[GNU Affero General Public License v3.0](../../../../LICENSE)

## 📚 引用
如果您在研究中使用 Stata-MCP，请使用以下格式之一引用此存储库：

### BibTeX
```bibtex
@software{sepinetam2025stata,
  author = {Song Tan},
  title = {Stata-MCP: Let LLM help you achieve your regression analysis with Stata},
  year = {2025},
  url = {https://github.com/sepinetam/stata-mcp},
  version = {1.13.0}
}
```

### APA
```
Song Tan. (2025). Stata-MCP: Let LLM help you achieve your regression analysis with Stata (Version 1.13.0) [Computer software]. https://github.com/sepinetam/stata-mcp
```

### Chicago
```
Song Tan. 2025. "Stata-MCP: Let LLM help you achieve your regression analysis with Stata." Version 1.13.0. https://github.com/sepinetam/stata-mcp.
```

## 📬 联系方式
电子邮件：[sepinetam@gmail.com](mailto:sepinetam@gmail.com)

或通过提交[拉取请求](https://github.com/sepinetam/stata-mcp/pulls)直接贡献！我们欢迎各种形式的贡献，从错误修复到新功能。

## ❤️ 致谢
作者诚挚感谢Stata官方团队给予的支持和授权测试开发使用的Stata License

## 📃 声明
项目里面涉及到的Stata指的是由[StataCorp LLC](https://www.stata.com/company/)开发的商业软件Stata。本项目与 StataCorp LLC 无隶属、关联或背书关系。本项目不包含 Stata 软件或其安装包，用户须自行从 StataCorp 获取并安装有效授权的 Stata 版本。本项目按 [AGPL-3.0](../../../../LICENSE) 许可发布，不对因使用本项目或与 Stata 相关操作产生的任何损失承担责任。


## ✨ 历史Star

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)