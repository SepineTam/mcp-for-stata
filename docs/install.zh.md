# 安装指南

本指南从选择安装方式开始，直到确认 AI 客户端能够调用 Stata。
第一次安装，建议使用下面的 `uvx` 方式。

## 安装前的准备

- 在本机安装并授权 Stata，确认 Stata 本身能够运行命令。
- 安装准备使用的 AI 客户端，例如 Claude Code、Codex 或 Cursor。
- 推荐方式需要 [uv](https://docs.astral.sh/uv/getting-started/installation/)，它提供 `uvx` 命令。通过 Python 包或源码安装时，需要 Python 3.11 或以上版本。
- 安装过程需要访问包下载源和 GitHub。MCP-for-Stata 不附带 Stata 软件及其许可证。

获取程序和接入客户端是两步：`uvx` 管理运行程序所需的 Python 环境；
`stata-mcp install` 写入客户端配置并安装受支持的附加组件。
它不会安装 AI 客户端本身。

## 选择安装方式

| 方式 | 适合谁 | 会做什么 |
|---|---|---|
| 让 Agent 帮忙安装 | 希望通过自然语言完成设置的用户 | Agent 使用自己的终端和文件工具，按本指南操作 |
| `uvx` 命令（推荐） | 大多数用户 | 运行安装器，无需手工管理 Python 环境 |
| 安装脚本 | 尚未安装 uv 的机器 | 检查 uv，按提示安装缺少的 uv，再调用客户端安装器 |
| Claude Code 原生插件 | 希望通过插件管理器管理组件的 Claude Code 用户 | 从 Claude 插件市场安装 `stata-toolbox` |
| 手动配置客户端 | 自定义启动命令、项目级配置或其他客户端 | 在客户端界面、命令行或配置文件中注册 MCP 服务 |
| 长期安装、可执行文件或源码 | 经常使用命令行或参与开发的用户 | 获得一个可以直接运行或手动接入客户端的本地程序 |

### 让 Agent 帮忙安装

将下面的话发给能够操作本机终端和配置文件的 Agent：

```text
阅读 GitHub 仓库 SepineTam/mcp-for-stata 中的 docs/install.zh.md。
为我正在使用的 AI 客户端安装 MCP-for-Stata，保留默认的 Stata addon，
不安装 extra。检查 Stata 可执行文件，保留我的现有配置，并告诉我哪些
组件已安装、哪些被跳过。等我重启客户端后，用 Stata 的 auto 示例数据
帮助我确认能够正常调用。
```

Agent 可能需要你说明客户端名称，或批准它在本机执行操作。
你仍需准备有效的 Stata 安装，并在完成配置后重启客户端。

## 推荐：使用 uvx 安装

### 1. 检查 uv 和 Stata

```bash
uv --version
uvx stata-mcp doctor --check stata_cli
```

如果找不到 uv，可先按 [uv 安装指南](https://docs.astral.sh/uv/getting-started/installation/)
安装，或使用下文的安装脚本。如果找不到 Stata，设置其可执行文件的完整路径，
不要填写目录或快捷方式：

```bash
uvx stata-mcp config set cli "/absolute/path/to/stata-executable"
uvx stata-mcp doctor --check stata_cli
```

macOS 和 Windows 用户还可以运行 `uvx stata-mcp discover` 查看候选安装位置。
该命令只寻找文件，不验证 Stata 许可证，也不执行分析。

### 2. 选择客户端

根据正在使用的客户端，选择一条命令：

```bash
uvx stata-mcp install -c codex
uvx stata-mcp install -c cc
uvx stata-mcp install -c cursor
```

`cc` 表示 Claude Code，`claude` 表示 Claude Desktop。其他客户端名称及别名见
[CLI 参考](cli.md)。需要配置安装器支持的所有目标时，可以运行：

```bash
uvx stata-mcp install --all
```

不带参数的 `install` 与 `install --all` 含义相同，不会只选择机器上已经安装的
客户端。Pi 因为需要单独的 MCP adapter，不包含在 `--all` 中，请显式使用
`-c pi`。Linux 不支持安装到 Claude Desktop。

### 3. 选择附加内容

默认安装基础 Stata MCP 和客户端支持的 Stata addon；extra 需要主动开启。

| 命令后半段 | 请求安装的内容 |
|---|---|
| `install -c codex` | 基础 MCP + addon |
| `install -c codex --no-addon` | 仅基础 MCP |
| `install -c codex --with-extra` | 基础 MCP + addon + extra |
| `install -c codex --no-addon --with-extra` | 基础 MCP + extra |

使用时在前面加上 `uvx stata-mcp`。这些开关同样适用于 `--all`。

- **addon** 来自 GitHub 的 `plugins/stata-toolbox/`：Stata Skill、写作规则，以及客户端支持时的 LSP 配置。
- **extra** 来自 GitHub 的 `plugins/external/`：DIP、NBER、Zotero 等科研 MCP 配置，以及这个目录中增加的 Skill。

每次安装先将 GitHub 的 `master` 解析为一个固定提交，再下载所选目录。
Skill 会连同脚本、引用文件和素材一起安装。安装器记录来源提交和文件哈希，
更新自己安装且未经修改的文件，跳过用户修改过的内容。下载失败时会提示警告，
已完成的基础 MCP 配置仍保留。

不同客户端支持的组件不同：Claude Code 可接收现有规则和 LSP 配置；其他
客户端可能只接收 Skill 和 MCP 配置。LSP 还要求语言服务器程序已在 PATH 中。
extra 只写入 MCP 配置，不会帮你安装或登录 Zotero 等第三方应用。
详细范围见 [CLI 参考中的组件支持表](cli.md)。

## 使用安装脚本

从仓库的 [scripts 目录](https://github.com/SepineTam/mcp-for-stata/tree/master/scripts)
下载对应文件。脚本会检查 uv，缺少时提供安装提示，然后调用
`uvx stata-mcp install`。没有指定客户端时，脚本使用 `--all`。

| 系统 | 文件 | 使用方式 |
|---|---|---|
| macOS | `install.command` | 在 Finder 中双击，或在终端运行 |
| macOS / Linux | `install.sh` | `bash install.sh -c codex` |
| Windows | `install.bat` | 在文件资源管理器中双击 |
| Windows PowerShell | `install.ps1` | `./install.ps1 -Client codex` |

macOS 如果提示缺少执行权限，可对下载的文件运行 `chmod +x install.command`。
Windows 如果阻止脚本执行，先检查文件和本机执行策略，不要直接修改全局策略。

包装脚本有自己的客户端列表和参数。需要较新的客户端名称、`--with-extra`、
`--no-addon` 或固定组件版本时，在 uv 可用后直接运行 `uvx` 安装命令。

## Claude Code 原生插件

这是通过 Claude 插件管理器管理 Stata 集成的另一条安装路径：

```bash
claude plugin marketplace add SepineTam/mcp-for-stata
claude plugin install stata-toolbox@stata-plugin-lib --scope user
claude plugin list
```

插件包含 MCP 配置、Skill 和 Stata LSP 配置。要使用 LSP，仍需单独安装语言
服务器可执行程序。安装这个原生插件不会同时开启 `plugins/external`。

与团队共享项目配置时，可将 `--scope user` 改为 `--scope project`。
初次安装选择原生插件或普通 MCP 安装中的一条路径，避免重复注册 Stata 服务。
普通 addon 安装器会单独管理规则；若已启用原生 `stata-toolbox`，则由原插件
管理 LSP。详情见 [Claude 插件指南](claude-plugin.md)。

## 手动配置客户端

需要项目级配置、其他客户端或直接运行本地程序时，可使用手动方式。
在客户端的 MCP 设置中选择本地服务或 stdio：

| 字段 | 填写内容 |
|---|---|
| 名称 | `stata-mcp` |
| 启动命令 | `uvx` |
| 参数 | `stata-mcp`、`server`，分别作为两个参数 |

使用标准 `mcpServers` JSON 格式的客户端，可将下面的条目合并到现有配置：

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "uvx",
      "args": ["stata-mcp", "server"]
    }
  }
}
```

Codex 使用 TOML：

```toml
[mcp_servers.stata-mcp]
command = "uvx"
args = ["stata-mcp", "server"]
```

不要用示例覆盖已有的其他服务或设置。各客户端的配置位置和格式不同，可通过
客户端界面查找，或参考 [客户端指南](clients.md)。手动注册只配置 MCP 服务，
不安装 addon 和 extra。桌面客户端找不到 `uvx` 时，可填写它的绝对路径。

## 其他获取程序的方式

### 长期安装命令行工具

```bash
uv tool install stata-mcp
stata-mcp --version
stata-mcp install -c codex
```

也可以安装到选定的 Python 环境：

```bash
python -m pip install stata-mcp
stata-mcp --version
```

当前自动安装器写入客户端的是 **uvx 启动命令**，即使安装器本身来自 pip、
源码或独立可执行文件，也一样。因此使用自动配置仍需要 uv。
若希望客户端直接使用本地程序，请手动填写该程序的绝对路径，参数使用
`["server"]`。这也能确保客户端使用你选定的 Python 环境，而非另一个 uvx 环境。

### Release 可执行文件

从 [GitHub Releases](https://github.com/SepineTam/mcp-for-stata/releases)
下载对应文件及其 `.sha256` 校验文件：

| 平台 | 文件 |
|---|---|
| macOS，Apple Silicon | `stata-mcp-macos-arm64` |
| Linux，x86-64 | `stata-mcp-linux-x86_64` |
| Windows，x86-64 | `stata-mcp-windows-x86_64.exe` |

核对下载文件的 SHA-256 与校验文件是否一致。macOS/Linux 需要给下载的文件
添加执行权限，再使用 `--version` 检查。将文件放在固定位置，手动配置客户端时
把它的绝对路径作为启动命令，把 `server` 作为参数。独立可执行文件不包含
Stata 软件及其许可证。

### 从源码安装

```bash
git clone https://github.com/SepineTam/mcp-for-stata.git
cd mcp-for-stata
uv sync
uv run stata-mcp --version
```

希望客户端运行这份源码时，手动将命令配置为 `uv`，参数依次填写
`run`、`--directory`、`/absolute/path/to/mcp-for-stata`、`stata-mcp`、`server`。
仅执行 `uv run stata-mcp install` 仍然会写入普通的 uvx 启动配置，
不会自动将客户端指向这份源码。

## 确认安装成功

使用推荐方式安装后，运行：

```bash
uvx stata-mcp doctor
uvx stata-mcp verify -c codex
```

根据 `verify --help` 支持的范围替换客户端名称。Doctor 检查运行环境；
verify 检查配置，不代表已建立真实 MCP 连接。直接使用本地程序时，
将 `uvx stata-mcp` 换成相应可执行文件。

重启客户端，确认 Stata MCP 工具出现，再发送：

```text
用 MCP-for-Stata 加载 Stata 自带的 auto 示例数据，将 price 对 mpg 和
weight 做回归。展示结果，并告诉我执行日志的路径。
```

这一步同时验证客户端、MCP 服务和 Stata。仅成功写入配置，还不等于通过这项
检查。被跳过的组件应单独查看；旧版客户端可能不支持 Skill，extra 服务也可能
需要完成自身的环境配置。

## 更新与固定版本

按获取程序时的方式更新：

```bash
# Refresh a uvx run
uvx --refresh stata-mcp --version

# Update a persistent uv tool
uv tool upgrade stata-mcp

# Update the selected Python environment
python -m pip install --upgrade stata-mcp
```

独立可执行文件通过替换为目标版本的 Release 文件更新。
源码安装通过 Git 更新代码，再执行 `uv sync`。

重新运行 `uvx stata-mcp install -c codex` 可检查 addon 更新；需要 extra 时加上
`--with-extra`。更新 Python 程序和更新 GitHub 组件是两项独立操作。
原生 Claude 插件使用 `claude plugin update stata-toolbox@stata-plugin-lib` 更新。

固定组件版本时，给 `install` 加上 `--addon-ref <tag-or-commit>`。
固定客户端运行的 MCP 包版本时，可手动配置启动命令为 `uvx`，参数为
`["--from", "stata-mcp==<version>", "stata-mcp", "server"]`，并替换占位版本号。
只给安装命令固定版本，并不会固定它写入客户端配置的运行版本。

## 常见安装问题

| 现象 | 下一步 |
|---|---|
| 找不到 `uvx` 或 `stata-mcp` | 安装后重新打开终端，检查 PATH，或填写程序的绝对路径 |
| 找不到 Stata | 用 `config set cli` 设置 Stata 可执行文件，再运行 `doctor --check stata_cli` |
| 客户端看不到工具 | 重启客户端并检查 MCP 状态，核对启动命令和配置范围 |
| GitHub 组件下载失败 | 查看警告及网络情况，再运行安装；基础 MCP 可能仍可使用 |
| addon 因本地修改而被跳过 | 检查自己的修改，安装器会保留这些内容 |
| Skill/LSP 文件存在但未加载 | 检查客户端的支持范围、版本，以及需要的语言服务器程序 |
| extra MCP 服务无法使用 | 单独检查该服务的依赖和身份认证 |

更多细节见 [故障排查](troubleshooting.md)、[配置指南](configuration.md)
及 [CLI 参考](cli.md)。
