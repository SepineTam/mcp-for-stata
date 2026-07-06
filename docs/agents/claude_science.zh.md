# 在 Claude Science 中使用

Claude Science 采用了更严格的沙箱（sandbox）策略，默认情况下无法读写主目录（`~`）下的文件。这会导致通过常规方式配置的 MCP-for-Stata 服务端在启动时直接报错：

```text
Couldn't load tools: MCP error -32000: Connection closed
--- stderr ---
Traceback ...
FileNotFoundError: [Errno 2] No such file or directory
```

该错误并非 MCP-for-Stata 本身异常，而是 Claude Science 的沙箱找不到可执行文件。下面给出两种解决方案。

## 完整流程

### 1. 安装 `stata-mcp`

```bash
uv tool install stata-mcp
```

### 2. 放行沙箱路径

运行以下命令，在 `~/.claude-science/config.toml` 中写入沙箱放行路径。脚本会先检查 `[sandbox]` 块是否已存在，避免重复写入。

```bash
mkdir -p ~/.claude-science
CONFIG_FILE="$HOME/.claude-science/config.toml"

if ! grep -q '^\[sandbox\]' "$CONFIG_FILE" 2>/dev/null; then
    cat >> "$CONFIG_FILE" <<EOF

[sandbox]
user_write_paths = [
  "$HOME/.local/bin",
  "$HOME/.local/share/uv/tools/stata-mcp",
]
EOF
    echo "已写入 $CONFIG_FILE"
else
    echo "[sandbox] 已存在，请手动检查 user_write_paths 是否包含以下路径："
    echo "  $HOME/.local/bin"
    echo "  $HOME/.local/share/uv/tools/stata-mcp"
fi
```

### 3. 在 Claude Science 中添加 MCP 服务

打开 Claude Science 的 MCP 配置界面，填写以下内容：

- **Name**：`Stata-MCP`
- **Command**：`~/.local/bin/stata-mcp`

保存后重启 Claude Science，即可正常加载 MCP-for-Stata 工具。

## 方案一：放行 `uv tool` 的安装路径

如果已经通过 `uv tool install stata-mcp` 安装，可执行文件和相关数据默认位于：

- `~/.local/bin/stata-mcp`
- `~/.local/share/uv/tools/stata-mcp`

需要在 Claude Science 的沙箱配置中显式放行这两个路径，使其可读可写。

在 `~/.claude-science/config.toml` 中添加如下内容：

```toml
[sandbox]
user_write_paths = [
  "~/.local/bin",
  "~/.local/share/uv/tools/stata-mcp",
]
```

保存后重启 Claude Science，再尝试加载 MCP-for-Stata 工具。

## 方案二：将 MCP-for-Stata 安装到非主目录

如果不想放行主目录，可以将 MCP-for-Stata 安装到一个沙箱默认允许访问的位置，例如项目目录或专门的工具目录。具体步骤后续补充。
