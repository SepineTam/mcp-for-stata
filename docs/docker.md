# Docker Guide

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
docker pull ghcr.io/sepinetam/stata-mcp
```

Or pull a specific version:
```bash
docker pull ghcr.io/sepinetam/stata-mcp:v1.13.33-s19
```

### DockerHub (Alternative)

```bash
docker pull sepinetam/stata-mcp
```

### Available Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release with Stata 18 |
| `v1.13.33-s17` | Version 1.13.33 with Stata 17 |
| `v1.13.33-s18` | Version 1.13.33 with Stata 18 |
| `v1.13.33-s19` | Version 1.13.33 with Stata 19 |

## Running Containers

### Basic Usage

```bash
docker run -i --rm \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v $(pwd):/workspace \
  ghcr.io/sepinetam/stata-mcp:latest
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
  ghcr.io/sepinetam/stata-mcp:latest
```

### Running in Background

For long-running tasks, you may want to run the container in background:

```bash
docker run -d --name stata-mcp-task \
  -v /path/to/stata.lic:/usr/local/stata/stata.lic \
  -v $(pwd):/workspace \
  ghcr.io/sepinetam/stata-mcp:latest
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

## Building from Source

If you want to build the image locally (mainly for developers):

```bash
# Clone the repository
git clone https://github.com/sepinetam/stata-mcp.git
cd stata-mcp

# Build with default Stata version
docker build -t stata-mcp:local .
```

### Using Local Installer

If you have the Stata installer tarball locally:

```bash
# Put installer in the project directory
cp /path/to/<installer-filename>.tar.gz ./Stata.tar.gz

# Build with local installer
docker build --build-arg STATA_INSTALL_URL=Stata.tar.gz -t stata-mcp:local .
```

### Using Remote URL

```bash
docker build --build-arg STATA_INSTALL_URL=<your-stata-installer-url> -t stata-mcp:local .
```

Note: Building locally still requires a valid Stata license at runtime.

## Tips

1. **License Security**: Keep your `stata.lic` file secure and never commit it to version control
2. **Data Persistence**: Always mount a workspace volume to persist your analysis results
3. **Resource Limits**: Use `--memory` and `--cpus` flags to limit container resources if needed:
   ```bash
   docker run -i --rm --memory=4g --cpus=2 \
     -v /path/to/stata.lic:/usr/local/stata/stata.lic \
     -v $(pwd):/workspace \
     ghcr.io/sepinetam/stata-mcp:latest
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
