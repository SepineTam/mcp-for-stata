# Claude 插件集成

## 概述

MCP-for-Stata 为 Claude Code 提供官方原生插件支持，目前 `stata-toolbox@stata-plugin-lib` 中集成了两个强大组件：

1. **MCP-for-Stata 服务器**：用于 Stata 执行的模型上下文协议服务器
2. **Stata LSP（Language Server Protocol）**：Stata do 文件的高级语言支持

此插件包名为 **stata-toolbox**，提供统一的实证研究开发环境，将 Stata 的分析能力与 AI 辅助和高级 IDE 功能相结合。

## 什么是 Claude Plugin？

Claude Plugin 是 Claude Code 中引入的插件系统，允许开发者打包和分发：

- **MCP 服务器**：向 Claude 暴露工具的模型上下文协议服务器
- **LSP 服务器**：用于增强编辑器支持的语言服务器协议服务器
- **Skills**：扩展 Claude 智能体能力的技能
- **配置**：预配置的最佳集成设置

插件系统实现复杂开发环境的一键安装，用可复现、版本控制的包替代手动配置。

## 插件结构

> 更多插件配置模式可在 Claude 的 [plugins-reference](https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema) 中找到。

```
.claude-plugin/
├── marketplace.json          # 插件注册表清单
└── plugins/
    └── stata-toolbox/       # 插件包
        └── plugin.json        # 插件配置
```

### 市场清单（`marketplace.json`）

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
      "description": "The official working package of MCP-for-Stata plugin, including mcp config and stata lsp."
    }
  ]
}
```

**字段：**
- `name`（string）：市场库标识符（kebab-case，无空格）
- `owner`（object）：作者信息
  - `name`（string）：作者姓名
  - `email`（string）：联系邮箱
- `plugins`（array）：插件包列表
  - `name`（string）：插件标识符
  - `source`（string）：插件目录的相对路径
  - `description`（string）：插件功能摘要

### 插件配置（`plugin.json`）

```json
{
  "name": "stata-toolbox",
  "version": "0.1.0",
  "description": "The official working package of MCP-for-Stata plugin, including mcp config and stata lsp.",
  "author": {
    "name": "Song Tan",
    "email": "sepinetam@gmail.com",
    "url": "https://www.sepinetam.com"
  },
  "homepage": "https://statamcp.com",
  "repository": "https://github.com/sepinetam/mcp-for-stata",
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

**配置分区：**

#### MCP 服务器配置

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

**command**：执行 MCP 服务器的命令。使用 `uvx` 允许直接运行已安装的 Python 包，无需激活虚拟环境。

**args**：传递给命令的命令行参数数组。`["stata-mcp"]` 指定要运行的包名。

#### LSP 服务器配置

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

> **注意**：您应该先通过 `pipx install "git+https://github.com/euglevi/stata-language-server.git"` 安装 `stata-language-server`。

**command**：LSP 服务器二进制可执行文件。必须在系统 PATH 中可用。

**args**：传递给 LSP 服务器的命令行参数数组。空数组表示无额外参数。

**extensionToLanguage**：将文件扩展名映射到语言标识符。`.do` 文件映射到 `stata` 语言以获得正确的 LSP 支持。

**settings**：LSP 特定配置对象。`stata` 键包含 Stata 语言服务器设置，用于代码补全、格式化和样式检查。

## 安装

### 前提条件

在安装插件之前，请确保满足以下要求：

1. **Claude Code**：通过官方安装程序安装
   ```bash
   # macOS/Linux
   curl -fsSL https://claude.ai/install.sh | bash

   # Windows
   irm https://claude.ai/install.ps1 | iex
   ```

2. **Stata**：有效的 Stata 17+ 许可证并安装了 Stata MP

3. **Python 包**：`stata-mcp` 包可用
   ```bash
   # 验证安装
   uvx stata-mcp doctor
   ```

4. **Stata LSP**：已安装语言服务器
   ```bash
   pipx install "git+https://github.com/euglevi/stata-language-server.git"
   ```

5. **uv**：包运行器（推荐）
   ```bash
   # 通过 homebrew 安装
   brew install uv

   # 或通过官方安装程序
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

### 安装方法

添加市场注册表并安装插件：

```bash
# 添加市场
claude plugin marketplace add sepinetam/stata-mcp

# 安装插件到用户范围（默认）
claude plugin install stata-toolbox

# 安装到项目范围（与团队共享）
claude plugin install stata-toolbox --scope project

# 安装到本地范围（gitignore）
claude plugin install stata-toolbox --scope local
```

插件自动使用当前目录作为 Stata 操作的工作目录。

### 验证

安装后，验证插件是否已加载：

```bash
# 列出已安装的插件
claude plugin list
```

### 工作原理

安装后，插件提供无缝集成：

**1. 自动加载**
Claude Code 自动检测：
- `.claude-plugin/marketplace.json` → 插件注册表
- `plugins/stata-toolbox/plugin.json` → 插件配置

**2. MCP 工具**
MCP-for-Stata 服务器暴露 Claude 可调用的工具：
- `stata_do`：执行 Stata 代码
- `write_dofile`：创建 do 文件
- `get_data_info`：分析数据集
- `help`：获取 Stata 命令文档
- 以及更多...

**3. LSP 功能**
Stata LSP 提供高级编辑器支持：
- **语法高亮**：增强的 .do 文件着色
- **补全**：自动建议 Stata 命令
- **悬停文档**：鼠标悬停在命令上获取帮助
- **错误检测**：实时语法验证
- **格式化**：自动格式化 .do 文件

### 示例工作流程

> 此部分由 AI 生成，使用前请审查。如果您想获得最佳结果，应该根据自己的偏好编辑 `~/.claude/CLAUDE.md`。

#### 论文复现

```markdown
> 从 "source/data/CPS_2018.dta" 加载数据集
> 使用 OLS 回归复现 Mincer (1974) 的表 3
> 将回归表导出为 LaTeX 格式

Claude：
1. 使用 get_data_info 了解数据集结构
2. 使用 write_dofile 创建 do 文件
3. 使用 stata_do 执行
4. 将表导出到 stata-mcp-result/
```

#### 快速假设检验

```markdown
> 检验 2008 年金融危机后教育回报是否增加
> 使用大学入学作为处理组的双重差分法

Claude：
1. 生成 DiD 规范
2. 使用事件研究设计运行 stata_do
3. 呈现带经济学解释的结果
```

## 比较：插件 vs 手动配置

### 手动配置

使用命令的传统方法：
```bash
claude mcp add stata-mcp -- uvx stata-mcp
```

或需要手动编辑 `.mcp.json`：

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

### 基于插件的配置

**使用插件：**

```bash
# 单命令安装
claude plugin marketplace add sepinetam/stata-mcp
claude plugin install stata-toolbox
```

### 比较

| 功能          | 手动配置                 | 插件安装                      |
|------------------|--------------------------------------|------------------------------------------|
| **设置**        | 手动编辑 `.mcp.json` 或命令 | 一键安装                 |
| **MCP 服务器**   | ✅                                    | ✅                                        |
| **LSP 服务器**   | ❌ 单独安装              | ✅ 包含                               |
| **团队共享** | ✅                                    | ✅                                        |
| **更新**      | 自动更新最新 MCP           | 自动更新 MCP，手动更新其他 |

## 架构

### 插件加载流程

```
1. Claude Code 启动
   ↓
2. 扫描 .claude-plugin/marketplace.json
   ↓
3. 解析插件注册表
   ↓
4. 加载每个插件的 plugin.json
   ↓
5. 注册 MCP 服务器
   ↓
6. 初始化 LSP 服务器
   ↓
7. 应用插件配置
   ↓
8. 插件可供使用
```

### 组件交互

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
    │         MCP-for-Stata Package           │
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

## 故障排除

### 插件未检测到

**症状：** 插件已安装但 Claude Code 不显示工具

**解决方案：**
1. 完全重启 Claude Code
2. 验证 marketplace.json 和 plugin.json 中的 JSON 语法
3. 检查文件权限（必须可读）
4. 确保插件正确安装
5. 运行 `claude plugin list` 验证

### MCP 服务器连接失败

**症状：** 工具显示错误 "Failed to connect to MCP server"

**诊断：**
```bash
# 独立测试 MCP 服务器
uvx stata-mcp doctor

# 检查 Stata 是否可访问
stata-se --version

# 验证 uvx 安装
uvx --version
```

**解决方案：**
1. 安装缺失的依赖：
   ```bash
   pip install stata-mcp
   ```

2. 验证 Stata 安装路径

3. 检查环境变量是否正确设置

### LSP 不工作

**症状：** .do 文件中没有语法高亮或补全

**诊断：**
```bash
# 检查 stata-language-server 是否已安装
which stata-language-server

# 测试 LSP 服务器
stata-language-server --help
```

**解决方案：**
1. 安装 stata-language-server：
   ```bash
   npm install -g stata-language-server
   ```

2. 验证文件扩展名映射：
   ```json
   {
     "extensionToLanguage": {
       ".do": "stata"
     }
   }
   ```

3. 检查 Claude Code 中的 LSP 日志

## 最佳实践

1. **验证安装**：安装前使用 `uvx stata-mcp doctor` 检查系统兼容性
2. **环境变量**：对敏感数据使用 `.env` 文件或项目设置
3. **文档**：维护带有研究指令的项目特定 CLAUDE.md
4. **版本更新**：保持插件更新以获取最新功能和错误修复

## 相关文档

- [配置指南](configuration.md) - 高级配置选项
- [安全文档](security.md) - 安全守卫系统
- [监控指南](monitoring.md) - 资源监控
- [MCP 工具参考](mcp/tools.md) - 可用工具
- [使用示例](usage.md) - 常见工作流程
- [客户端配置](clients.md) - 替代客户端设置

## 许可证和归属

stata-toolbox 插件是 MCP-for-Stata 项目的一部分。

- **许可证**：AGPL-3.0
- **版权**：(c) 2026 Song Tan (Sepine Tam), Inc.
- **作者**：Song Tan (sepinetam@gmail.com)

**Stata LSP**：由 [euglevi](https://github.com/euglevi/stata-language-server) 版权所有，采用 [MIT 许可证](https://github.com/euglevi/stata-language-server/blob/main/LICENSE)

该插件集成了独立开发的组件：
- **MCP-for-Stata Server**：[GitHub 仓库](https://github.com/sepinetam/mcp-for-stata)
- **Stata LSP**：[GitHub 仓库](https://github.com/euglevi/stata-language-server)

---

**文档版本**：1.0.0
**最后更新**：2025-02-12
**维护者**：Song Tan (sepinetam@gmail.com)
