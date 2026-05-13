#!/bin/bash
#
# Stata-MCP Installation Script for macOS and Linux
# https://github.com/sepinetam/stata-mcp
#
# Usage:
#   ./install.sh                    # Install to all supported clients
#   ./install.sh -c claude          # Install to Claude Desktop only
#   ./install.sh -c claude -c cc    # Install to Claude Desktop and Claude Code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Supported clients
CLIENTS=("claude" "cc" "gemini" "cursor" "cline" "codex" "opencode" "openclaw")

# Parse command line arguments
declare -a TARGET_CLIENTS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--client)
            TARGET_CLIENTS+=("$2")
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --client <name>  Target client (can be used multiple times)"
            echo "                       Supported: ${CLIENTS[*]}"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Install to all clients"
            echo "  $0 -c claude          # Install to Claude Desktop only"
            echo "  $0 -c claude -c cc    # Install to Claude Desktop and Claude Code"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo ""
echo "======================================"
echo "    Install Stata-MCP ..."
echo "======================================"
echo ""

# Add common uv installation paths to PATH
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Check if uv is installed
check_uv() {
    if command -v uv &> /dev/null; then
        echo -e "${GREEN}[✓] uv is installed${NC}"
        return 0
    else
        return 1
    fi
}

# Install uv
install_uv() {
    echo -e "${YELLOW}[!] uv is not installed${NC}"
    echo ""
    read -p "Do you want to install uv? [Y/n]: " choice
    case "$choice" in
        n|N|no|No|NO)
            echo -e "${RED}[✗] Installation cancelled.${NC}"
            exit 1
            ;;
        *)
            echo ""
            MAX_RETRIES=3
            RETRY_COUNT=0
            while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                echo "Installing uv... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
                if curl -LsSf --connect-timeout 30 https://astral.sh/uv/install.sh | sh; then
                    break
                else
                    RETRY_COUNT=$((RETRY_COUNT + 1))
                    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                        echo -e "${YELLOW}[!] Installation failed, retrying in 3 seconds...${NC}"
                        sleep 3
                    else
                        echo -e "${RED}[✗] Failed to install uv after $MAX_RETRIES attempts.${NC}"
                        echo "    Please install it manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
                        exit 1
                    fi
                fi
            done

            # Source the shell profile to make uv available
            if [ -f "$HOME/.cargo/env" ]; then
                source "$HOME/.cargo/env"
            elif [ -f "$HOME/.local/share/uv/env" ]; then
                source "$HOME/.local/share/uv/env"
            fi

            # Re-check if uv is now available
            if command -v uv &> /dev/null; then
                echo -e "${GREEN}[✓] uv installed successfully${NC}"
            else
                # Try to add uv to PATH directly
                export PATH="$HOME/.local/bin:$PATH"
                if command -v uv &> /dev/null; then
                    echo -e "${GREEN}[✓] uv installed successfully${NC}"
                else
                    echo -e "${RED}[✗] Failed to install uv. Please install it manually:${NC}"
                    echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
                    exit 1
                fi
            fi
            ;;
    esac
}

# Main installation logic
main() {
    # Step 1: Check and install uv
    if ! check_uv; then
        install_uv
    fi

    # Step 2: Install to clients
    if [ ${#TARGET_CLIENTS[@]} -eq 0 ]; then
        # No specific clients specified, install to all
        echo ""
        echo "Installing to all supported clients..."
        uvx stata-mcp install --all
    else
        # Install to specified clients
        for client in "${TARGET_CLIENTS[@]}"; do
            if [[ " ${CLIENTS[*]} " =~ " ${client} " ]]; then
                echo ""
                echo "Installing to $client..."
                uvx stata-mcp install -c "$client"
            else
                echo -e "${RED}[✗] Unknown client: $client${NC}"
                echo "    Supported clients: ${CLIENTS[*]}"
            fi
        done
    fi

    # Step 3: Remind user to restart
    echo ""
    echo "======================================"
    echo -e "${GREEN}[✓] Installation complete!${NC}"
    echo "======================================"
    echo ""
    echo "Please restart your AI client(s) for the changes to take effect."
    echo ""
    echo "For more information, visit: https://www.statamcp.com or https://github.com/sepinetam/stata-mcp"
    echo ""
}

main
