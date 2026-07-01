# MCP-for-Stata

**将 Stata 集成到你的智能体中。**

> 针对处于中国大陆用户的提示：如果出现失败，大概率是因为网络问题，请考虑使用 THU 的镜像，具体配置详见 [包下载缓慢或失败](troubleshooting.zh.md#包下载缓慢或失败)。

## 🆕 MCP-for-Stata 现已支持 OpenClaw

**MCP-for-Stata 现已支持 OpenClaw！** MCP-for-Stata 提供独立的 CLI 工具，将以下命令粘贴到你的 OpenClaw 中，它会自动安装 skill。

```text
Install `stata-skill` from ClawHub by @SepineTam.
```

完整文档请参阅 [OpenClaw 集成指南](agents/openclaw.md)。

## 快速开始

> 系统要求：[uv](https://docs.astral.sh/uv/getting-started/installation/) 或 python 3.11+
> 如果你没有 `uv` 但有 `python`，可以通过 `pip install uv` 安装。

首先，你应该检查你的设备是否被 stata-mcp 支持。
```bash
uvx stata-mcp doctor
```
如果每项检查都通过，你就可以开始使用 stata-mcp 了。
如果提示找不到 STATA_CLI，你可以查看 [StataFinder](core/stata/finder.md#not-found) 来解决。

通用配置文件（json）
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

### 在 Claude Code 中使用

我们推荐将 MCP-for-Stata 与 [Claude Code](https://github.com/anthropics/claude-code) 配合使用，因为它具有出色的智能体能力。

在使用之前，请确保你已经安装了 Claude Code。如果你不知道如何安装，请访问 [GitHub](https://github.com/anthropics/claude-code)。

打开你的终端，`cd` 到你的工作目录，然后运行：

```bash
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp
```

这将在你的工作目录中创建一个包含 MCP 配置的 `.mcp.json` 文件。

#### 使用场景

- **论文复现**：复现经济学论文中的实证研究
- **快速假设检验**：通过回归分析验证经济学假设
- **Stata 学习助手**：通过分步 Stata 解释学习计量经济学
- **代码组织**：审查和优化现有的 Stata do 文件
- **结果解读**：理解复杂的统计输出和回归结果

详细使用指南请访问 [agents/claude_code.md](agents/claude_code.md)。

---

如果你想探索更多[客户端](clients.md)，请访问客户端文档。

## 文档

### 核心文档

- **[概述](overview.md)**：架构、设计理念和集成模式
- **[使用指南](usage.md)**：常见使用模式和示例
- **[配置](configuration.md)**：包含所有选项的完整配置指南
- **[客户端](clients.md)**：支持的 MCP 客户端和设置说明
- **[Claude 插件](claude-plugin.md)**：官方 Claude Code 插件集成指南

### 高级功能

- **[Docker](docker.md)**：在容器化环境中运行 MCP-for-Stata
- **[安全守卫](security.md)**：危险命令的安全验证系统
- **[监控系统](monitoring.md)**：RAM 监控和资源限制
- **[故障排查](troubleshooting.zh.md)**：常见问题与网络问题解决方案

### 核心组件

- **[Stata 集成](core/stata/)**
  - [StataDo](core/stata/do.md)：Do 文件执行
  - [StataFinder](core/stata/finder.md)：Stata 可执行文件检测
  - [Stata Help](core/stata/help.md)：命令文档
  - [包安装](core/stata/package.md)：SSC 和 GitHub 包

- **[MCP 工具](mcp/tools.md)**：可用的 MCP 工具和用法
- **[MCP 资源](mcp/resources.md)**：MCP 资源和能力

### 客户端集成

- **[Claude Code 集成](agents/claude_code.md)**：详细的 Claude Code 设置

## 快速链接

### 面向用户

- [开始使用](#quickly-start)
- [配置指南](configuration.md)
- [安全文档](security.md)
- [监控设置](monitoring.md)

### 面向开发者

- [架构概述](overview.md)
- [MCP 工具参考](mcp/tools.md)
- [核心组件](core/stata/)

### 配置

- [基本配置](configuration.md#configuration-file)
- [安全设置](configuration.md#security-section)
- [监控设置](configuration.md#monitor-section)
- [环境变量](configuration.md#environment-variables)
