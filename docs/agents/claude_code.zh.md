# 在 Claude Code 中使用

> **已废弃**:MCP-for-Stata 内置的 agent 模式自 v1.16.x 起已带 `FutureWarning`,将在后续版本移除。请改用 MCP server 模式(`stata-mcp server` 或 `stata-mcp install -c <客户端>`),并使用宿主 AI 客户端自带的 agent 能力。

我们非常高兴能编写这份关于 MCP-for-Stata 与 Claude Code 结合使用的文档。在我日常的研究工作中，Claude Code 是我最常使用的工具之一。

如果尚未安装，可以访问 [Claude Code](https://code.claude.com/docs/en/quickstart) 进行安装。

> 系统要求：
> - [Stata](https://www.stata.com) 17+
> - [uv](https://docs.astral.sh/uv/getting-started/installation/) 或 Python 3.11+
> - Claude Code

## 快速开始

首先，检查 MCP-for-Stata 是否与您的设备兼容：

```bash
uvx stata-mcp doctor
```

然后，创建您的项目。我们建议将所有项目放在同一目录下。例如，我们使用 `~/Documents/StataProjects` 作为项目目录。

```bash
cd ~/Documents/StataProjects
claude mcp add stata-mcp --env STATA_MCP__CWD=$(pwd) --scope project -- uvx --directory $(pwd) stata-mcp
```

> 建议：请确保目录路径中不包含空格、表情符号或中文字符等特殊字符。

项目创建成功后，目录结构如下：

```text
my_first_project/            # 项目目录
├── .statamcp/               # MCP-for-Stata 生成的所有文件
│   ├── stata-mcp-dofile/    # do 文件
│   ├── stata-mcp-log/       # 日志文件
│   ├── stata-mcp-result/    # 某些命令（如 `outreg2`）的结果保存在此
│   └── stata-mcp-tmp/       # 临时文件，如数据信息描述
│   └── .gitignore           # git 忽略文件
└── CLAUDE.md                # 项目全局指令文件

```
