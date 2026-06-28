<div align="center">
  <a href="https://aidea-labs.com/mcp-for-stata">
    <img src="https://example-data.statamcp.com/logo_with_name.jpg" alt="MCP-for-Stata：将 Stata 集成到你的智能体中" width="300"/>
  </a>
</div>

# MCP-for-Stata：将 Stata 集成到你的智能体中
让 Claude Code，Codex，OpenClaw 等 AI 智能体直接调用你设备中的 Stata 在本地 **安全地** 进行数据分析。

> Stata 是 StataCorp LLC 的注册商标。本项目为独立社区开发工具，与 StataCorp LLC 无任何关联、背书或赞助关系。

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
## 🆕 动态
- 更多内容请关注微信公众号：[Why I made it?](https://mp.weixin.qq.com/s/VYkykdDgfPMa5KN0_1BeFQ)，以及 [8 figures find out Stata-MCP](https://mp.weixin.qq.com/s/RKPKA4OWAM5SeZmGtbMRew)
- 🦞 **OpenClaw 支持**：独立的 OpenClaw 集成 CLI 工具（`stata-mcp tool`），详见 [OpenClaw 指南](https://sepinetam.github.io/mcp-for-stata/agents/openclaw.md)
- ✨ **Claude Code 插件支持**：官方插件包，包含 MCP 服务器和 Stata LSP 集成
- 在 Claude Code 中使用 MCP-for-Stata，请查看 [Claude Code 高级用法](#advanced-claude-code)，或在 Codex 中使用请查看 [Codex 高级用法](#advanced-codex)

> 想了解我们的**最新研究**？查看最新研究报告。

<details>
<summary>寻找其他资源？</summary>

> **MCP 或 AI 相关的 Stata 工具**
> - 基于会话的 Stata MCP 服务器，[mcp-stata](https://github.com/tmonk/mcp-stata)
> - IDE 集成（VSCode 或 Cursor）[在 VScode 里使用 Stata](https://github.com/hanlulong/stata-mcp)。分不清区别？💡 [查看对比](#对比)
>
> **数据集与信息**
> - [STOP Dataset](https://opendata.ai4cssci.com)：StataMCP-Team 开放数据项目 📊，我们开源了一套面向社会科学研究的综合数据集，旨在推动 AI 驱动和数据驱动的研究范式。
</details>

<details>
<summary>为什么使用 AGPL 3.0 License？</summary>

AGPL 3.0 License 是开源协议中的一种，它不会影响您的日常使用，该协议允许您免费使用、修改和分发本软件，但必须遵守相关条款，如保留源代码版权信息等。

**说明**：尽管我们希望尽可能让所有人都能从开源中获益，但我们很遗憾地宣布无法继续保持 Apache-2.0 License。由于有人直接抄袭本项目并标榜其为项目维护者，我们不得不将 License 更改为 AGPL-3.0，以防止有人滥用本项目进行违背项目初心的事情。

原因如下：

**背景**：@jackdark425 的[仓库](https://github.com/jackdark425/aigroup-stata-mcp)直接抄袭了本项目并标榜为项目唯一维护者。我们欢迎基于 fork 的开源协作，包括但不限于添加新的 feature、修改已有 bug 或对项目提出宝贵的意见，但坚决反对抄袭和虚假署名行为。

**更新**：侵权项目已通过 GitHub DMCA 被下架，[查看 DMCA 下架详情](https://github.com/github/dmca/blob/master/2025/12/2025-12-30-stata-mcp.md)。

</details>

## 💡 快速开始
### 🚀 一键安装所有客户端！
无需配置，无需手动编辑 JSON。一条命令即可为 **所有受支持的 agent**（Claude Code、Codex、OpenClaw、Cursor、Gemini CLI 等）安装 MCP-for-Stata：

```bash
uvx stata-mcp install --all
```

<details>
<summary>支持的智能体 🤖</summary>
基于我们自己的经验和测试，我们推荐使用 Claude Code、Codex 和 OpenClaw。
我们发现 Claude 和 DeepSeek 是在任何框架下表现最好的两个模型。

| 智能体                     | 标签      | 命令                               |
|---------------------------|----------|-----------------------------------|
| Claude Desktop            | claude   | uvx stata-mcp install -c claude   |
| Claude Code               | cc       | uvx stata-mcp install -c cc       |
| Gemini CLI                | gemini   | uvx stata-mcp install -c gemini   |
| Cursor                    | cursor   | uvx stata-mcp install -c cursor   |
| Cline (VScode 扩展)       | cline    | uvx stata-mcp install -c cline    |
| Codex CLI & Codex Desktop | codex    | uvx stata-mcp install -c codex    |
| OpenCode                  | opencode | uvx stata-mcp install -c opencode |
| OpenClaw                  | openclaw | uvx stata-mcp install -c openclaw |

</details>

如果你还没有安装 `uv`，请[查看 uv 安装指南](https://docs.astral.sh/uv/getting-started/installation)进行安装。
或者，使用我们的测试版安装脚本（如未安装 `uv` 会自动安装）：

**macOS / Linux：**
```bash
curl -fsSL https://raw.githubusercontent.com/SepineTam/mcp-for-stata/master/scripts/install.sh | bash
```

**Windows (PowerShell)：**
```powershell
irm https://raw.githubusercontent.com/SepineTam/mcp-for-stata/master/scripts/install.ps1 | iex
```

如果你不知道如何使用它们，可以[下载安装脚本](https://github.com/SepineTam/mcp-for-stata/tree/master/scripts)并在设备上双击运行。Windows 用户使用 `install.bat`，macOS 用户使用 `install.command`。

<a name="advanced-claude-code"></a>

### 高级用法 - Claude Code
由于我们发现 Claude Code 凭借其出色的智能体能力是最适合 MCP-for-Stata 的工具，我们推荐使用它，以下是多种高级用法：

在使用之前，请确保你已经安装了 `Claude Code`，如果不知道如何安装，请访问 [GitHub](https://github.com/anthropics/claude-code)。

通常情况下，你可以全局安装一次 MCP-for-Stata，运行：
```bash
claude mcp add stata-mcp --scope user -- uvx stata-mcp
```

之后就不需要再关注它了。

<details>
<summary>本地安装并与合作伙伴共享</summary>

如果你只想在特定工作区本地安装，可以 `cd` 到工作目录，然后运行：
```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope local -- uvx --directory $(pwd) stata-mcp
```

安装后不会有明显变化，你可以输入 `claude` 并输入 `/mcp` 来查看状态。

此外，协作是研究的重要组成部分。你可以使用以下命令与合著者共享 MCP 配置：
```bash
claude mcp add stata-mcp --scope project -- uvx stata-mcp
```
在你的工作目录中，你会找到一个名为 `.mcp.json` 的文件，你的 MCP 配置将放置于此。

</details>

然后，你就可以在 Claude Code 中使用 MCP-for-Stata 了。以下是一些使用场景：

- **论文复现**：复现经济学论文中的实证研究
- **快速假设检验**：通过回归分析验证经济学假设
- **Stata 学习助手**：通过逐步的 Stata 讲解学习计量经济学
- **代码整理**：审查和优化现有的 Stata do-file
- **结果解读**：理解复杂的统计输出和回归结果

如果你在 IDE 中使用 Claude Code（无论是集成终端还是 Claude Code 扩展），可以安装我们的插件，包含 [MCP-for-Stata](https://github.com/sepinetam/mcp-for-stata) 和由 @euglevi 维护的 [Stata LSP](https://github.com/euglevi/stata-language-server)。

```bash
# 添加 MCP-for-Stata 应用市场
claude plugin marketplace add SepineTam/mcp-for-stata

# 在本地、项目或用户范围内安装插件
claude plugin install stata-toolbox -s project
```

> 语言服务器为 AI 生成的 Stata 代码提供更好的语法感知和补全功能，从而提高输出质量。我们在遵守其许可证的前提下打包了 LSP，并对原作者给予完整的署名。

<a name="advanced-codex"></a>

### 高级用法 - Codex
我们发现许多研究人员正在使用 Codex 作为他们的智能体，因此我们也为 Codex 用户提供了使用说明。

我认为研究人员使用的不是 Codex CLI 而是 Codex Desktop，因此我们可以说配置 MCP-for-Stata 比其他智能体更简单。

你只需要说 `Install MCP-for-Stata for yourself globally from https://www.statamcp.com or visit https://github.com/SepineTam/mcp-for-stata`，然后在它显示准备就绪后重启你的 Codex Desktop 即可。

此外，如果你想手动安装，有以下两种方式：

#### A. 在 Codex Desktop GUI 中安装
1. 打开你的 Codex Desktop 应用
2. 点击左下角的 `Settings`
3. 在左侧找到 `MCP servers`
4. 点击 `Add server`
5. 填写以下内容：
    ```
    Name: stata-mcp
    Command to launch: uvx
    Arguments: stata-mcp
    ```
6. 点击 `Save`
7. 然后重启你的 Codex Desktop 即可开始使用。

#### B. 使用 Codex CLI 安装
对于 CLI 模式，只需在终端中运行以下命令：
```bash
uvx stata-mcp install -c codex
```

或者使用
```bash
codex mcp add stata-mcp -- uvx stata-mcp
```

### 其他客户端
> 标准配置要求：请确保 Stata 已安装在默认路径，并且 Stata CLI 存在（适用于 macOS 和 Linux）。

标准配置 JSON 如下，你可以通过添加环境变量来自定义配置。
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

更多详细使用信息，请访问[使用指南](https://sepinetam.github.io/mcp-for-stata/usage)。

### 前提条件
- [uv](https://github.com/astral-sh/uv) - 包安装器和虚拟环境管理器
- Claude Code、Codex、OpenClaw 或其他智能体
- Stata 许可证
- 你的 LLM API-KEY

如果你想检查你的设备是否受支持，可以运行：
```bash
uvx stata-mcp doctor
```

它会显示你设备的基本信息，并检查你的设置是否受支持。

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

> 注意：
> 1. 如果你位于中国并遇到下载缓慢的问题，请参考[解决方案](docs/troubleshooting.zh.md#包下载缓慢或失败)。
> 2. Claude 是 MCP-for-Stata 的最佳选择，对于中文用户，我推荐使用 DeepSeek 作为模型提供商，因为它性价比高且功能强大，在中国提供商中评分最高。如果你感兴趣，请访问报告[如何使用 StataMCP 提升你的社会科学研究](https://statamcp.com/reports/2025/09/21/stata_mcp_a_research_report_on_ai_assisted_empirical_research)。

## 对比

目前有多个与 Stata 相关的 MCP 项目。下表由 Claude Code 在直接分析每个代码库后生成。

| 功能 | [MCP-for-Stata](https://aidea-labs.com/mcp-for-stata) (本项目) | [haoyu-haoyu/stata-ai-fusion](https://github.com/haoyu-haoyu/stata-ai-fusion) | [hanlulong/stata-mcp](https://github.com/hanlulong/stata-mcp) | [tmonk/mcp-stata](https://github.com/tmonk/mcp-stata) |
|---|---|---|---|---|
| **最佳适用** | 智能体驱动分析（Claude Code、Codex、OpenClaw） | 交互式会话、图表导出、精选 Stata 知识库 | 在 VSCode 中自行编写和运行 Stata 代码的用户 | 研究工作流（复现、稳健性检验、发表 QA） |
| **智能体** | 全部支持 | 全部支持 | VSCode 窗口必须保持激活 | 全部支持 |
| **类型** | MCP 服务器 + CLI 工具包 | MCP 服务器 + Skill 知识库 + VS Code 扩展 | VSCode 扩展（本地服务器，非独立 MCP） | 基于会话的 MCP 服务器 |
| **执行方式** | 通过子进程运行 do-file | pexpect 交互式会话 + 批处理降级 | 通过本地 4000 端口的 IDE 嵌入式运行器 | pystata（Stata 17+） |
| **安全性** | 命令守卫 + 内存监控 | 取消命令 + 会话清理 | — | — |
| **数据分析** | CSV、DTA、XLSX、SPSS 处理器 | 会话内 `inspect_data` / `codebook` | — | 会话内 `describe` / `codebook` |
| **日志** | 文本 + SMCL 读取器 | 会话内 `search_log` | — | 内置日志读取器 |
| **图表** | — | 自动检测 + `export_graph` PNG/SVG/PDF | — | 导出、缓存、SVG/PNG |
| **CLI 支持** | 原生支持（与 MCP 服务器相同工具） | 基础入口点 | — | — |
| **会话** | — | 多命名会话，支持空闲超时 | — | 多会话、后台任务 |
| **IDE 插件** | — | 原生 VS Code / Cursor 扩展 | 原生 VSCode / Cursor | Stata Workbench (VS Code) |
| **技能 / 知识库** | 面向 MCP-for-Stata 的工具型技能（742 行） | 5,653 行通用 Stata 技能知识库 | — | 20+ 专业研究技能（因果推断、复现、发表 QA 等） |
| **安装方式** | `uvx stata-mcp install` | `uvx --from stata-ai-fusion stata-ai-fusion` | VS Code 应用市场 | `uvx` 或安装脚本 |

## 📝 文档
> MCP-for-Stata 文档请访问 https://sepinetam.github.io/mcp-for-stata

### 核心文档
- **[完整文档](https://sepinetam.github.io/mcp-for-stata/)**：包含所有功能的完整文档站点
- **[配置指南](https://sepinetam.github.io/mcp-for-stata/configuration)**：基于 TOML 的统一配置系统
- **[安全守卫](https://sepinetam.github.io/mcp-for-stata/security)**：危险命令的安全验证
- **[监控系统](https://sepinetam.github.io/mcp-for-stata/monitoring)**：内存监控和资源限制
- **[架构概览](https://sepinetam.github.io/mcp-for-stata/overview)**：系统设计和集成模式

### 主要功能
- **[安全守卫](https://sepinetam.github.io/mcp-for-stata/security)**：拦截危险命令（`!`、`shell`、`erase` 等）
- **[内存监控](https://sepinetam.github.io/mcp-for-stata/monitoring)**：通过可配置限制防止内存耗尽
- **[统一配置](https://sepinetam.github.io/mcp-for-stata/configuration)**：TOML 配置 + 环境变量
- 跨平台支持（macOS、Windows、Linux）
- 自动日志捕获和错误报告

## 🐛 报告问题
如果你遇到任何 bug 或有功能请求，请[提交 issue](https://github.com/sepinetam/mcp-for-stata/issues/new)。

## 📄 许可证
[GNU Affero General Public License v3.0](LICENSE)

## 📚 引用
如果你在研究中使用了 MCP-for-Stata，并且它确实对你有帮助，你可以使用以下格式之一引用本仓库：

### BibTeX
```bibtex
@software{sepinetam2025stata,
  author = {Song Tan},
  title = {MCP-for-Stata: Integrate Stata into your agent},
  year = {2025},
  url = {https://github.com/sepinetam/mcp-for-stata},
  version = {1.18.0}
}
```

### APA
```
Song Tan. (2025). MCP-for-Stata: Integrate Stata into your agent (Version 1.18.0) [Computer software]. https://github.com/sepinetam/mcp-for-stata
```

### Chicago
```
Song Tan. 2025. "MCP-for-Stata: Integrate Stata into your agent." Version 1.18.0. https://github.com/sepinetam/mcp-for-stata.
```

## 📬 联系方式
邮箱：[sepinetam@gmail.com](mailto:sepinetam@gmail.com)

或直接通过提交 [Pull Request](https://github.com/sepinetam/mcp-for-stata/pulls) 来贡献代码！我们欢迎各种形式的贡献，从 bug 修复到新功能。

## 📃 声明
Stata 是 [StataCorp LLC](https://www.stata.com/company/) 的注册商标。本项目（MCP-for-Stata）是一个独立的开源工具，与 StataCorp LLC 无任何关联、背书或赞助关系。本项目不分发 Stata 软件、其源代码或任何安装包。用户必须自行从 StataCorp LLC 或其授权经销商处购买并安装有效许可的 Stata 副本。

本项目基于 [AGPL-3.0](LICENSE) 许可证授权。项目维护者不对因使用本项目代码或文档而造成的任何损失或损害承担责任。

## ✨ Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=sepinetam/stata-mcp&type=Date)](https://www.star-history.com/#sepinetam/stata-mcp&Date)
