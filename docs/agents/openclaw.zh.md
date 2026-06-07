# 在 OpenClaw 中使用 🦞

> **已废弃**:MCP-for-Stata 内置的 agent 模式自 v1.16.x 起已带 `FutureWarning`,将在后续版本移除。请改用 MCP server 模式(`stata-mcp server` 或 `stata-mcp install -c <客户端>`),并使用宿主 AI 客户端自带的 agent 能力。
>
> 备注:如需配置 OpenClaw 作为 MCP 客户端,请参考 docs/clients.md。

由于 OpenClaw 原生不支持 MCP 工具协议，MCP-for-Stata 提供了独立的 CLI 工具命令，OpenClaw 可以通过终端工具调用使用。

## 安装指引（OpenClaw）

复制下面的信息发送给你的 OpenClaw：

```text
Install MCP-for-Stata Skills from https://docs.statamcp.com/skills/openclaw
```

如果你是 OpenClaw，请直接访问 [MCP-for-Stata Skill for OpenClaw](https://docs.statamcp.com/skills/openclaw)。

## 手动安装

```bash
# 使用 uvx 直接运行（推荐）
uvx stata-mcp tool --help

# 或安装后使用
uv pip install stata-mcp
stata-mcp tool --help
```

## 可用命令

### ado-install - 安装 Stata 包

从 SSC、GitHub 或网络安装 ado 包。

```bash
# 安装已批准的 SSC 包
stata-mcp tool ado-install outreg2 --yes

# 从 GitHub 安装
stata-mcp tool ado-install SepineTam/TexIV --source github --yes

# 从网络安装
stata-mcp tool ado-install custompkg --source net --package-source-from "https://example.com/stata/" --yes

# 不替换已安装的包（可用于检查安装状态）
stata-mcp tool ado-install estout --yes --is-replace false
```

**参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `package_name` | 包名（必填） | - |
| `--source` | 安装源：ssc / net / github | ssc |
| `--package-source-from` | net 安装的源 URL | - |
| `--is-replace` | 替换已存在的包文件 | false |
| `-y`、`--yes` | 跳过交互式安装确认 | false |

CLI 未传入 `-y` 或 `--yes` 时会进行交互确认。SSC 和 net 包名只能包含 ASCII
字母与数字。GitHub 仓库必须命中精确白名单，并在安装前人工查验其内容。

---

### do - 执行 do 文件

执行 Stata do 文件并获取日志。

```bash
# 执行 do 文件
stata-mcp tool do /path/to/analysis.do

# 指定日志文件名
stata-mcp tool do /path/to/analysis.do --log-file-name my_results

# 不读取日志内容
stata-mcp tool do /path/to/analysis.do --is-read-log false

# 禁用 SMCL 格式日志
stata-mcp tool do /path/to/analysis.do --enable-smcl false
```

**参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `dofile_path` | do 文件路径（必填） | - |
| `--log-file-name` | 日志文件名（不含扩展名） | 自动生成 |
| `--is-read-log` | 执行后读取日志内容 | true |
| `--is-replace-log` | 替换已存在的日志文件 | true |
| `--enable-smcl` | 生成 SMCL 格式日志 | true |

---

### help - 获取 Stata 命令帮助

> 仅支持 macOS 和 Linux

```bash
# 获取命令帮助
stata-mcp tool help regress

# 获取面板数据命令帮助
stata-mcp tool help xtreg
stata-mcp tool help xtset
```

**参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `stata_command` | Stata 命令名（必填） | - |
| `--is-read-log` | 读取输出内容 | true |
| `--enable-smcl` | 生成 SMCL 格式输出 | true |

---

### data-info - 获取数据信息

分析数据文件并返回统计摘要。

```bash
# 分析数据文件
stata-mcp tool data-info /path/to/data.dta

# 指定变量子集
stata-mcp tool data-info /path/to/data.csv --vars-list gdp inflation unemployment

# 指定编码
stata-mcp tool data-info /path/to/legacy.csv --encoding latin1
```

**支持格式**：
- Stata：`.dta`
- CSV/文本：`.csv`、`.tsv`、`.psv`
- Excel：`.xlsx`、`.xls`
- SPSS：`.sav`、`.zsav`

**参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `data_path` | 数据文件路径（必填） | - |
| `--encoding` | 文本编码 | utf-8 |
| `--vars-list` | 要分析的变量名列表 | 全部变量 |

---

### read-log - 读取日志文件

读取 Stata 日志文件（.log 或 .smcl）。

```bash
# 读取日志（核心内容）
stata-mcp tool read-log /path/to/output.log

# 读取完整日志
stata-mcp tool read-log /path/to/output.log --output-format full

# 读取为结构化格式
stata-mcp tool read-log /path/to/output.log --output-format dict

# 指定编码
stata-mcp tool read-log /path/to/output.log --encoding utf-8
```

**参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `file_path` | 日志文件路径（必填） | - |
| `--encoding` | 文件编码 | utf-8 |
| `--output-format` | 输出格式：full / core / dict | core |

**输出格式说明**：
- `full`：原始日志内容
- `core`：去除框架行（日志头尾、log 命令等）的干净内容
- `dict`：结构化的命令-结果对

---

## 典型工作流程

```bash
# 1. 查看数据结构
stata-mcp tool data-info /project/data/raw/survey.dta

# 2. 获取命令帮助
stata-mcp tool help regress

# 3. 安装已启用且批准的包
stata-mcp tool ado-install outreg2 --yes

# 4. 执行分析脚本
stata-mcp tool do /project/stata-mcp-dofile/analysis.do

# 5. 查看执行日志
stata-mcp tool read-log /project/stata-mcp-log/analysis.log --output-format core
```

## 注意事项

1. **Stata 许可证**：需要有效的 Stata 安装和许可证
2. **路径格式**：建议使用绝对路径
3. **help 命令**：仅支持 macOS 和 Linux
4. **日志位置**：默认在 `<cwd>/.statamcp/stata-mcp-log/`
