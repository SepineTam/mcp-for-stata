# Docker 指南

> **重要许可证声明**
>
> Stata® 是 StataCorp LLC 的注册商标和版权软件。本项目**不**分发 Stata 软件。
>
> 我们的 Docker 镜像基于 [AEA Data Editor 的 Stata 镜像](https://github.com/AEADataEditor/docker-stata)构建，该镜像已获得 StataCorp 的 gracious 许可，可以分发 Stata 二进制文件（不含许可证文件）。
>
> **您必须拥有有效的 Stata 许可证才能使用这些镜像。** 使用这些 Docker 镜像即表示您同意遵守 StataCorp 的[最终用户许可协议](https://www.stata.com/order/end-user-license-agreement/)。

> **注意**：如果您不熟悉 Docker，我们建议直接使用 `uvx stata-mcp` 来使用 Stata-MCP。

Stata-MCP 提供官方 Docker 镜像，用于在沙盒环境中运行。这适用于：

- **隔离**：在不影响本地环境的情况下运行 Stata-MCP
- **可复现性**：在不同机器间保持一致的环境
- **并行任务**：同时运行多个独立的 Stata 任务
- **CI/CD**：将 Stata 分析集成到自动化流水线中

## 前提条件

- **Docker** 已安装并运行
- **Stata 许可证文件**（`stata.lic`）- 您唯一需要准备的文件

## 可用镜像

Stata-MCP 镜像可从两个注册表获取：

### GitHub Container Registry（推荐）

```bash
docker pull ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
```

### DockerHub（替代）

```bash
docker pull sepinetam/stata-mcp_19_5_mp:latest
```

### 镜像命名约定

```
stata-mcp_{VERSION}_{EDITION}
```

- **VERSION**：`19_5`（StataNow 19.5）、`18_5`（StataNow 18.5）、`18`（Stata 18）
- **EDITION**：`mp`（多处理器）、`se`（标准版）、`be`（基础版）

### 可用镜像

> 您选择的镜像应基于您的 Stata 许可证。

| 镜像 | 描述 |
|-------|-------------|
| `stata-mcp_19_5_mp` | StataNow 19.5 多处理器（推荐） |
| `stata-mcp_19_5_se` | StataNow 19.5 标准版 |
| `stata-mcp_19_5_be` | StataNow 19.5 基础版 |
| `stata-mcp_18_5_mp` | StataNow 18.5 多处理器 |
| `stata-mcp_18_5_se` | StataNow 18.5 标准版 |
| `stata-mcp_18_5_be` | StataNow 18.5 基础版 |
| `stata-mcp_18_mp` | Stata 18 多处理器 |
| `stata-mcp_18_se` | Stata 18 标准版 |
| `stata-mcp_18_be` | Stata 18 基础版 |

## 运行容器

### 基本用法

```bash
docker run -i --rm \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v $(pwd):/workspace \
  ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
```

### 参数说明

| 参数 | 描述 |
|-----------|-------------|
| `-i` | 交互模式，保持 STDIN 打开 |
| `--rm` | 容器退出时自动删除 |
| `-v /path/to/stata.lic:/usr/local/stata/stata.lic` | 挂载您的 Stata 许可证文件 |
| `-v $(pwd):/workspace` | 将当前目录挂载为工作区 |

### 带自定义工作目录

```bash
docker run -i --rm \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v /path/to/your/project:/workspace \
  ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
```

### 后台运行

对于长时间运行的任务，您可能需要在后台运行容器：

```bash
docker run -d --name stata-mcp-task \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v $(pwd):/workspace \
  ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
```

查看日志：

```bash
docker logs -f stata-mcp-task
```

停止并删除：

```bash
docker stop stata-mcp-task
docker rm stata-mcp-task
```

## MCP 客户端配置

### 通用配置

要将 Docker 镜像与 MCP 客户端（Claude Code、Cursor、Cline 等）配合使用，请配置您的 MCP 设置：

```json
{
  "mcpServers": {
    "stata-mcp": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "/path/to/stata.lic:/usr/local/stata/stata.lic",
        "-v",
        "/path/to/workspace:/workspace",
        "ghcr.io/sepinetam/stata-mcp_19_5_mp"
      ]
    }
  }
}
```

替换：
- `/path/to/stata.lic` - 您的 Stata 许可证文件的绝对路径
- `/path/to/workspace` - 您的工作目录的绝对路径

### Claude Code CLI

或使用 Claude Code CLI 添加基于 Docker 的 MCP 服务器：

```bash
claude mcp add stata-mcp -s local -- docker run --rm -i \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v $(pwd):/workspace \
  ghcr.io/sepinetam/stata-mcp_19_5_mp
```

### 使用 Stata-MCP CLI 安装

或使用 Stata-MCP CLI 安装基于 Docker 的 MCP 服务器：

```bash
uvx stata-mcp sandbox-install \
  --version 19_5 \
  --edition mp \
  --tag latest \
  -l /path/to/stata.lic \
  -c claude
```

#### CLI 选项

| 选项 | 默认值 | 描述 |
|--------|---------|-------------|
| `-V, --version` | `19_5` | Stata 版本（`19_5`、`18_5`、`18`） |
| `-e, --edition` | `mp` | Stata 版本类型（`mp`、`se`、`be`） |
| `--tag` | `latest` | Docker 镜像标签 |
| `-l, --license-file` | （必填） | Stata 许可证文件路径 |
| `-c, --client` | `claude` | 目标客户端（`claude`、`cc`、`cursor`、`cline`） |
| `--work-dir` | `./` | 工作目录 |
| `--cpus` | （无） | CPU 核心限制 |
| `--memory` | （无） | 内存限制 |

## 从源代码构建

如果您想在本地构建镜像（主要针对开发者）：

```bash
# 克隆仓库
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

# 使用特定 Stata 版本构建
docker build \
  --build-arg CAPTURE_VERSION=19_5 \
  --build-arg BASIS=mp \
  -t stata-mcp:local .
```

### 构建参数

| 参数 | 默认值 | 描述 |
|----------|---------|-------------|
| `CAPTURE_VERSION` | `19_5` | Stata 版本（`19_5`、`18_5`、`18`） |
| `BASIS` | `mp` | Stata 版本类型（`mp`、`se`、`be`） |
| `TAG` | `2026-01-14` | AEA 基础镜像标签 |

注意：本地构建在运行时仍需要有效的 Stata 许可证。

## 提示

1. **许可证安全**：保护好您的 `stata.lic` 文件，永远不要将其提交到版本控制
2. **数据持久化**：始终挂载工作区卷以持久化分析结果
3. **资源限制**：如果需要，使用 `--memory` 和 `--cpus` 标志限制容器资源：
   ```bash
   docker run -i --rm --memory=4g --cpus=2 \
     -v /path/to/stata.lic:/usr/local/stata/stata.lic \
     -v $(pwd):/workspace \
     ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
   ```

## 故障排除

### 许可证未找到

```
Error: Stata license not found
```

确保许可证文件路径正确且文件存在。

### 权限被拒绝

```
Error: Permission denied accessing /workspace
```

在 Linux 上，您可能需要调整文件权限或使用 `--user` 标志。

### 容器立即退出

检查日志以获取错误消息：

```bash
docker logs <container_id>
```
