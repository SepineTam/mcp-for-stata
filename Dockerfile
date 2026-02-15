FROM ubuntu:22.04

LABEL author="sepinetam"
LABEL description="Stata-MCP Official Docker image for running Stata-MCP in a sandboxed environment"
LABEL url="https://www.statamcp.com"
LABEL license="AGPL-3.0"

# We are thanks to Duke University for the publicly available Stata installer.
# Note: Stata 17+ is required for Stata-MCP.
# Available versions:
#   Stata 19: https://public.econ.duke.edu/stata/installers/19/StataNow19Linux64.tar.gz
#   Stata 18: https://public.econ.duke.edu/stata/installers/18/Stata18Linux64.tar.gz
#   Stata 17: https://public.econ.duke.edu/stata/installers/17/Stata17Linux64.tar.gz
ARG STATA_INSTALL_URL=https://public.econ.duke.edu/stata/installers/19/StataNow19Linux64.tar.gz

ADD ${STATA_INSTALL_URL} /tmp/stata.tar.gz
RUN mkdir -p /tmp/stata_installer && \
    tar -xzf /tmp/stata.tar.gz -C /tmp/stata_installer && \
    rm /tmp/stata.tar.gz

# Install stata to /usr/local/stata
RUN mkdir -p /usr/local/stata
RUN cd /usr/local/stata && printf "y\ny\n" | /tmp/stata_installer/install
RUN rm -rf /tmp/stata_installer

# Make all Stata executables runnable (mp, se, be)
RUN chmod +x /usr/local/stata/stata-mp
RUN chmod +x /usr/local/stata/stata-se
RUN chmod +x /usr/local/stata/stata

# Add Stata to PATH
ENV PATH="/usr/local/stata:${PATH}"

# Stata CLI, can be overridden at runtime with -e STATA_CLI=stata-se
ENV STATA_CLI=stata-mp

# Install uv
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory and environment
WORKDIR /workspace
ENV STATA_MCP__CWD=/workspace

CMD ["uvx", "stata-mcp", "-t", "stdio"]
