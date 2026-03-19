# Stata-MCP 概述

## 🆕 Stata-MCP 现已支持 OpenClaw

**Stata-MCP 现已支持 OpenClaw！** Stata-MCP 提供独立的 CLI 工具：

```bash
# 执行 do 文件
stata-mcp tool do /path/to/analysis.do

# 获取数据信息
stata-mcp tool data-info /path/to/data.dta

# 安装包
stata-mcp tool ado-install outreg2

# 读取日志文件
stata-mcp tool read-log /path/to/output.log
```

完整文档请参阅 [OpenClaw 集成指南](agents/openclaw.md)。

## 什么是 Stata-MCP 和 Stata？

**Stata-MCP** 是一个模型上下文协议（Model Context Protocol, MCP）服务器，它将大语言模型（LLM）与 Stata 连接起来，实现自主计量经济学分析和统计计算。基于 FastMCP 框架构建，Stata-MCP 将 Stata 全面分析能力作为结构化工具暴露出来，供 LLM 以编程方式调用，将自然语言查询转换为可复现的 Stata 工作流程。

### 为什么选择 Stata-MCP？

Stata 仍然是实证社会科学研究中的主流分析引擎。仅在中国经济学领域，超过 80% 的已发表文章是实证研究，其中超过 98.4% 使用 Stata 进行分析。这种普及源于 Stata 成熟的生态系统、方法论的完整性和已发表研究的可复现性。

Stata-MCP 解决了 AI 辅助研究中的一个关键空白：虽然现代 LLM 擅长代码生成和统计推理，但它们缺乏针对 Stata 等领域特定工具的原生执行环境。通过实现 MCP 协议，Stata-MCP 实现了：

- **确定性执行**：LLM 生成的 Stata 代码在可控、可复现的环境中执行
- **方法论严谨性**：访问 Stata 经验证的计量经济学实现确保分析完整性
- **工作流程编排**：复杂的多步骤分析（数据清洗 → 估计 → 可视化）成为自动化流水线
- **跨平台兼容性**：跨 macOS、Windows 和 Linux 环境的统一抽象层

## 架构概述

Stata-MCP 通过四个架构层运行：

### 1. **协议层（MCP 服务器）**
基于 `FastMCP` 的服务器（`src/stata_mcp/__init__.py`）实现模型上下文协议，将 Stata 操作作为结构化工具暴露。每个工具定义：
- 带类型验证的输入参数模式
- 供 LLM 消费的输出序列化
- 错误处理和日志基础设施
- 有状态操作的资源注册

### 2. **执行层（Stata 集成）**
平台特定的 Stata 控制器管理命令执行：
- **`StataFinder`**：跨操作系统定位 Stata 可执行文件（macOS：`/Applications/Stata/`，Windows：`Program Files`，Linux：系统 PATH）
- **`StataController`**：管理 Stata 进程生命周期、命令调用和退出代码监控
- **`StataDo`**：处理带日志捕获和错误报告的 do 文件执行

### 3. **安全与监控层**
生产部署的高级安全功能：
- **[安全守卫](security.md)**：针对危险命令（shell 执行、文件删除等）验证 dofile
- **[监控系统](monitoring.md)**：带自动进程终止的实时 RAM 监控
- **基于黑名单的验证**：在执行前阻止危险操作
- **资源限制**：防止内存耗尽和系统不稳定

### 4. **配置层**
带分层优先级的统一配置管理：
- **[配置系统](configuration.md)**：位于 `~/.statamcp/config.toml` 的 TOML 配置文件
- **环境变量**：针对特定会话覆盖设置
- **优先级**：环境变量 > 配置文件 > 默认值
- **分区**：DEBUG、SECURITY、PROJECT、MONITOR

### 5. **应用层（模式与工具）**
两种主要操作模式：

#### **MCP 服务器模式**（默认）
作为 stdio/HTTP/SSE 服务器运行，响应来自 MCP 兼容客户端的工具调用请求。工具包括：

| 工具 | 用途 |
|------|---------|
| `stata_do` | 执行 do 文件并获取日志 |
| `write_dofile` | 创建带时间戳的 do 文件 |
| `get_data_info` | 分析 CSV/DTA 文件并生成统计摘要 |
| `help` | 检索 Stata 命令文档（缓存） |
| `ssc_install` | 从 SSC/GitHub/net 源安装包 |
| `read_file` | 带编码支持的通用文件读取 |

#### **智能体模式**（`agent run` 命令）
用于对话分析的交互式 REPL 智能体：
- 用于多轮会话的 Read-Eval-Print Loop (REPL) 接口
- 基于 SQLite 的会话管理，用于对话历史
- 通过 `agent run <path>` 支持自定义工作目录
- 用于模型配置的环境变量（`STATA_MCP_MODEL`、`STATA_MCP_API_KEY`）
- 支持任何 OpenAI 兼容的 API 端点

## 数据处理流水线

Stata-MCP 实现了支持多种格式的多态数据分析系统：

### **DataInfo 架构**
抽象基类 `DataInfoBase` 及其格式特定实现：
- **`DtaDataInfo`**：原生 Stata `.dta` 格式，带元数据提取
- **`CsvDataInfo`**：CSV/TSV/PSV 文件，带编码检测和类型推断
- **`ExcelDataInfo`**：Excel 工作簿（`.xlsx`、`.xls`），带工作表选择
- **`SpssDataInfo`**：SPSS 数据文件（`.sav`、`.zsav`）- *v1.14.0 新增*

### **统计指标**
可配置的指标计算（通过 `~/.statamcp/config.toml` 或环境变量）：
- **默认**：观测值、均值、标准误、最小值、最大值
- **扩展**：Q1、Q3、偏度、峰度、唯一值采样

### **缓存策略**
使用 MD5 哈希的内容可寻址缓存：
```
~/.statamcp/.cache/data_info__<name>_<ext>__hash_<suffix>.json
```
检测到内容变化时自动进行缓存失效。

## 项目结构约定

Stata-MCP 为可复现研究强制执行标准化的目录布局：

```text
~/Documents/stata-mcp-folder/
├── stata-mcp-log/      # Stata 执行日志（带时间戳）
├── stata-mcp-dofile/   # 生成的 do 文件（ISO 8601 时间戳）
├── stata-mcp-result/   # 命令输出（outreg2、esttab 导出）
└── stata-mcp-tmp/      # 临时文件（数据信息缓存）
```

对于 AI 辅助研究项目，推荐模板（`stata-mcp --init`）创建：

```text
<project_name>/
├── .claude/
│   ├── skills/              # 自定义 Claude Code skills
│   └── settings.local.json  # MCP 服务器注册
├── source/
│   ├── data/
│   │   ├── raw/             # 不可变的源数据
│   │   ├── processing/      # 中间数据集
│   │   └── final/           # 可直接分析的数据
│   ├── figs/                # 出版图表
│   └── tabs/                # 出版表格
├── stata-mcp-folder/        # Stata-MCP 工作目录
└── CLAUDE.md                # 项目特定指令
```

## 集成模式

### **在 AI 客户端中**
MCP 兼容客户端（Claude Code、Cline、Continue）在其配置中将 Stata-MCP 注册为服务器：

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

### **在 Python 智能体中**
Stata-MCP 智能体可以作为工具嵌入到其他智能体工作流程中：

```python
from stata_mcp.agent_as import StataAgent
from agents import Agent, Runner

# 初始化 Stata 智能体并转换为工具
stata_agent = StataAgent()
stata_tool = stata_agent.as_tool

# 嵌入到更大的智能体工作流程中
research_assistant = Agent(
    name="Research Assistant",
    instructions="You help with economic research using Stata",
    tools=[stata_tool]
)

# 运行智能体
result = await Runner.run(
    research_assistant,
    "Analyze the relationship between education and income"
)
```

### **终端 REPL**
交互式分析会话：

```python
from stata_mcp.agent_as import REPLAgent

agent = REPLAgent(work_dir="~/analysis")
agent.run()  # 启动交互式 REPL
```

## 跨平台支持

| 平台 | Stata 检测 | 包安装 | 帮助系统 |
|----------|----------------|---------------------|-------------|
| macOS | `/Applications/Stata/StataMP` | 原生 CLI | ✅ 缓存 |
| Windows | `Program Files` 注册表 | Do 文件委托 | ❌ 不支持 |
| Linux | PATH 中的 `stata-mp` | 原生 CLI | ✅ 缓存 |

## 设计理念

1. **不可变性**：源文件保持不变；所有操作创建带时间戳的产物
2. **故障安全**：优雅降级（例如，`append_dofile` 在源文件缺失时创建新文件）
3. **可复现性**：确定性路径、自动日志记录和缓存失效
4. **可扩展性**：用于自定义工具和数据格式处理器的插件架构
5. **安全优先**：
   - **安全守卫**：在执行前阻止危险命令
   - **路径验证**：将文件操作限制在工作目录
   - **资源监控**：通过 RAM 监控防止内存耗尽
   - **沙盒执行**：隔离的执行环境以确保安全

## 高级功能

### **安全守卫** ✅
自动针对危险命令验证所有 dofile 代码：
- 阻止 shell 执行（`!`、`shell`、`xshell` 等）
- 防止文件删除操作（`erase`、`rm`）
- 停止不受信任的代码执行（`run`、`do`、`include`）
- 可通过[安全设置](configuration.md#security-section)配置

### **RAM 监控** ✅
实时监控 Stata 进程内存使用：
- 执行期间跟踪 RAM 使用
- 超过限制时自动终止进程
- 每个项目可配置 RAM 限制
- 守护线程架构，开销极小
- 详见[监控文档](monitoring.md)

### **统一配置** ✅
分层配置系统：
- 基于 TOML 的配置文件（`~/.statamcp/config.toml`）
- 环境变量覆盖
- 分区：DEBUG、SECURITY、PROJECT、MONITOR
- 详见[配置文档](configuration.md)

### **沙盒系统**（暂不支持）
使用 Jupyter 内核的替代执行后端，适用于没有 Stata 许可证的环境或测试目的。

### **多语言支持**（暂不支持）
用于本地化错误消息和文档的可配置语言设置。

## 引用和致谢

Stata-MCP 由实证研究社区开发，旨在将 AI 辅助与领域特定的分析工具连接起来。欢迎通过 [GitHub 仓库](https://github.com/sepinetam/stata-mcp)提交贡献、错误报告和功能请求。
