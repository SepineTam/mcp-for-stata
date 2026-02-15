ARG CAPTURE_VERSION=19_5
ARG BASIS=mp
ARG TAG=2026-01-14

FROM dataeditors/stata${CAPTURE_VERSION}-${BASIS}:$TAG

LABEL author="sepinetam"
LABEL description="Stata-MCP Official Docker image for running Stata-MCP in a sandboxed environment"
LABEL url="https://www.statamcp.com"
LABEL license="AGPL-3.0"

# Set user to avoid permission issues
USER root

# Stata CLI, can be overridden at runtime with -e STATA_CLI=stata-se
ENV STATA_CLI=stata-${BASIS}

# Install uv
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Install Stata-MCP to system
COPY . /app
WORKDIR /app
RUN uv sync

# Set working directory and environment
WORKDIR /workspace
ENV STATA_MCP__CWD=/workspace

CMD ["/app/.venv/bin/stata-mcp", "-t", "stdio"]
