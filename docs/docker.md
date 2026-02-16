# Docker Guide

> **Important License Notice**
>
> Stata® is a registered trademark and copyrighted software of StataCorp LLC. This project does **not** distribute Stata software.
>
> Our Docker images are built on top of the [AEA Data Editor's Stata images](https://github.com/AEADataEditor/docker-stata), which have been graciously provided with permission from StataCorp to distribute the Stata binaries (without license files).
>
> **You must possess a valid Stata license to use these images.** By using these Docker images, you agree to comply with StataCorp's [End-User License Agreement](https://www.stata.com/order/end-user-license-agreement/).

Stata-MCP provides official Docker images for running in sandboxed environments. This is useful for:

- **Isolation**: Run Stata-MCP without affecting your local environment
- **Reproducibility**: Consistent environment across different machines
- **Parallel Tasks**: Run multiple independent Stata tasks simultaneously
- **CI/CD**: Integrate Stata analysis into automated pipelines

## Prerequisites

- **Docker** installed and running
- **Stata license file** (`stata.lic`) - the only file you need to prepare

## Available Images

Stata-MCP images are available from two registries:

### GitHub Container Registry (Recommended)

```bash
docker pull ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
```

### DockerHub (Alternative)

```bash
docker pull sepinetam/stata-mcp_19_5_mp:latest
```

### Image Naming Convention

```
stata-mcp_{VERSION}_{EDITION}
```

- **VERSION**: `19_5` (StataNow 19.5), `18_5` (StataNow 18.5), `18` (Stata 18)
- **EDITION**: `mp` (Multi-processor), `se` (Standard), `be` (Basic)

### Available Images

> The image which you chose is based on your Stata license. 

| Image | Description |
|-------|-------------|
| `stata-mcp_19_5_mp` | StataNow 19.5 Multi-processor (recommended) |
| `stata-mcp_19_5_se` | StataNow 19.5 Standard |
| `stata-mcp_19_5_be` | StataNow 19.5 Basic |
| `stata-mcp_18_5_mp` | StataNow 18.5 Multi-processor |
| `stata-mcp_18_5_se` | StataNow 18.5 Standard |
| `stata-mcp_18_5_be` | StataNow 18.5 Basic |
| `stata-mcp_18_mp` | Stata 18 Multi-processor |
| `stata-mcp_18_se` | Stata 18 Standard |
| `stata-mcp_18_be` | Stata 18 Basic |

## Running Containers

### Basic Usage

```bash
docker run -i --rm \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v $(pwd):/workspace \
  ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
```

### Parameter Explanation

| Parameter | Description |
|-----------|-------------|
| `-i` | Interactive mode, keeps STDIN open |
| `--rm` | Automatically remove container when it exits |
| `-v /path/to/stata.lic:/usr/local/stata/stata.lic` | Mount your Stata license file |
| `-v $(pwd):/workspace` | Mount current directory as workspace |

### With Custom Working Directory

```bash
docker run -i --rm \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v /path/to/your/project:/workspace \
  ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
```

### Running in Background

For long-running tasks, you may want to run the container in background:

```bash
docker run -d --name stata-mcp-task \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v $(pwd):/workspace \
  ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
```

Check logs:

```bash
docker logs -f stata-mcp-task
```

Stop and remove:

```bash
docker stop stata-mcp-task
docker rm stata-mcp-task
```

## MCP Client Configuration

### General Configuration

To use the Docker image with MCP clients (Claude Code, Cursor, Cline, etc.), configure your MCP settings:

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

Replace:
- `/path/to/stata.lic` - Absolute path to your Stata license file
- `/path/to/workspace` - Absolute path to your working directory

### Claude Code CLI

Or use Claude Code CLI to add the Docker-based MCP server:

```bash
claude mcp add stata-mcp -s local -- docker run --rm -i \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v $(pwd):/workspace \
  ghcr.io/sepinetam/stata-mcp_19_5_mp
```

### Install with Stata-MCP CLI

Or use the Stata-MCP CLI to install Docker-based MCP server:

```bash
uvx stata-mcp sandbox-install \
  --version 19_5 \
  --edition mp \
  --tag latest \
  -l /path/to/stata.lic \
  -c claude
```

#### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `-V, --version` | `19_5` | Stata version (`19_5`, `18_5`, `18`) |
| `-e, --edition` | `mp` | Stata edition (`mp`, `se`, `be`) |
| `--tag` | `latest` | Docker image tag |
| `-l, --license-file` | (required) | Path to Stata license file |
| `-c, --client` | `claude` | Target client (`claude`, `cc`, `cursor`, `cline`) |
| `--work-dir` | `./` | Working directory |
| `--cpus` | (none) | CPU core limit |
| `--memory` | (none) | Memory limit |

## Building from Source

If you want to build the image locally (mainly for developers):

```bash
# Clone the repository
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

# Build with specific Stata version
docker build \
  --build-arg CAPTURE_VERSION=19_5 \
  --build-arg BASIS=mp \
  -t stata-mcp:local .
```

### Build Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `CAPTURE_VERSION` | `19_5` | Stata version (`19_5`, `18_5`, `18`) |
| `BASIS` | `mp` | Stata edition (`mp`, `se`, `be`) |
| `TAG` | `2026-01-14` | AEA base image tag |

Note: Building locally still requires a valid Stata license at runtime.

## Tips

1. **License Security**: Keep your `stata.lic` file secure and never commit it to version control
2. **Data Persistence**: Always mount a workspace volume to persist your analysis results
3. **Resource Limits**: Use `--memory` and `--cpus` flags to limit container resources if needed:
   ```bash
   docker run -i --rm --memory=4g --cpus=2 \
     -v /path/to/stata.lic:/usr/local/stata/stata.lic \
     -v $(pwd):/workspace \
     ghcr.io/sepinetam/stata-mcp_19_5_mp:latest
   ```

## Troubleshooting

### License Not Found

```
Error: Stata license not found
```

Make sure the license file path is correct and the file exists.

### Permission Denied

```
Error: Permission denied accessing /workspace
```

On Linux, you may need to adjust file permissions or use `--user` flag.

### Container Exits Immediately

Check the logs for error messages:

```bash
docker logs <container_id>
```
