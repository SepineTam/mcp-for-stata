# Stata Finder

## 工作原理

由于大多数用户将 Stata 安装在默认位置，我们创建了 StataFinder 模块来自动定位您设备上的 Stata 可执行文件，从而在大多数情况下实现无缝体验。

### 检测流程

1. **环境变量优先**：首先检查是否设置了 `STATA_CLI` 环境变量；如果已设置，直接使用它
2. **自动检测**：如果未设置环境变量，根据操作系统自动搜索 Stata
3. **版本选择**：当发现多个 Stata 版本时，自动选择最高优先级的版本

### 平台差异

- **macOS**：搜索 `/usr/local/bin` 目录和 `/Applications` 中的 Stata.app
- **Windows**：搜索默认安装路径（Program Files）和所有可用驱动器
- **Linux**：搜索 `/usr/local/bin` 及其包含 "stata" 的子目录

### 版本优先级

当系统上存在多个 Stata 版本时，选择规则如下：

1. **版本类型**：MP > SE > BE > IC > default
2. **版本号**：在同一版本类型内，选择更高版本（如 Stata 19 > Stata 18）


## 找不到？

如果 `uvx stata-mcp doctor` 提示找不到您的 Stata，别担心。如果您确定设备上有 Stata，请按照以下步骤解决。

### macOS
1. 打开您的 `Stata.app`，您可以在 Apple 标志右侧找到 `Stata/MP 19.0` 或其他类似版本，点击它。
2. 然后，点击 `install terminal utility`。
3. 现在，您可以关闭 Stata，再次运行 `uvx stata-mcp doctor`。"
4. 如果仍然提示 `not found`，您可以打开终端并运行 `which stata-mp`（如果您的版本是 StataSE 或 StataBE，可以将 `stata-mp` 替换为 `stata-se` 或 `stata-be`）。
5. 将环境变量 `STATA_CLI` 设置为您在第 4 步获得的路径。

例如：
```bash
sepinetam@sepine-macbook ~ % which stata-mp
/usr/local/bin/stata-mp
sepinetam@sepine-macbook ~ % export STATA_CLI="/usr/local/bin/stata-mp"
sepinetam@sepine-macbook ~ % uvx stata-mcp doctor

stata-mcp v1.17.0 — Doctor Report

  [PASS] os: macOS (Darwin 25.3.0, arm64)
  [PASS] python: 3.11.11 (/Users/sepinetam/Documents/Github/stata-mcp/.venv/bin/python3)
  [PASS] uv: uv 0.11.13 (Homebrew 2026-05-11 aarch64-apple-darwin) (/opt/homebrew/bin/uv)
  [PASS] dependencies: all required packages available
  [PASS] stata_cli: /usr/local/bin/stata-mp (from env)
  [PASS] stata_execution: OK (0.2s)
  [PASS] config: /Users/sepinetam/.statamcp/config.toml (loaded)
  [PASS] working_dir: /Users/sepinetam/Documents/Github/stata-mcp (writable)
  [PASS] guard: enabled, loaded 27 rules
  [PASS] monitor: disabled (psutil available)
  [PASS] pypi: reachable (1.74s)
  [PASS] cleanup: 0 old files (0 B) found; cleanup disabled (CLEAN_LOG_DAYS=-1)

Summary: 12 passed, 0 failed, 0 warning(s), 0 skipped
```

此外，将配置写入 `~/.zshrc`，如下所示：
```bash
cat >> ~/.zshrc <<'EOF'
# Stata CLI path
export STATA_CLI="$(command -v stata-mp 2>/dev/null)"
EOF

source ~/.zshrc
echo "$STATA_CLI"
```

### Linux
1. 如果您使用的是没有 GUI 的 Linux 机器，您应该知道您的 `stata-mp` 可执行文件位于何处，我将假设您是一位有经验的计算机用户。
2. 只需将环境变量 `STATA_CLI` 设置为您的 `stata-mp` 可执行文件路径，然后再次运行 `uvx stata-mcp doctor`。如果没有错误，则配置成功。

### Windows
Windows 的配置相对复杂，但核心方法与 macOS 和 Linux 类似。您需要找到您的 `Stata.exe`（或类似命名的）文件，然后将 `Stata.exe` 路径设置为环境变量 `STATA_CLI`。关于如何在 Windows 中设置环境变量有很多在线资源，您可以自己搜索。以下是如何找到实际的 `Stata.exe` 文件：
1. 按键盘上的 Windows 键，搜索 "Stata"，找到您正在使用的 Stata。
2. 右键点击并选择 "打开文件位置"。此时，此目录中通常只有两个文件——这些不是实际的可执行文件。再次右键点击并选择"打开文件位置"以找到真正的可执行文件，然后将其路径设置为环境变量 `STATA_CLI`。
3. 再次运行 `uvx stata-mcp doctor`。如果没有错误，则配置成功。
