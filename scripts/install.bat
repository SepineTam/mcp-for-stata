@echo off
setlocal
set "STATA_MCP_INSTALL_SCRIPT=%~f0"
powershell -ExecutionPolicy Bypass -NoProfile -Command "$f=$env:STATA_MCP_INSTALL_SCRIPT; $lines = Get-Content $f | Select-Object -Skip 6; $script = $lines -join ""`n""; & ([scriptblock]::Create($script))"
pause
exit /b

# --- PowerShell script starts below this line ---
#
# Stata-MCP Installation Script for Windows
# https://github.com/sepinetam/stata-mcp
#
# Usage:
#   .\install.bat                    # Install to all supported clients
#   .\install.bat -Client claude     # Install to Claude Desktop only
#   .\install.bat -Client claude,cc  # Install to Claude Desktop and Claude Code

param(
    [string[]]$Client = @(),
    [switch]$Help
)

# Supported clients
$supportedClients = @("claude", "cc", "gemini", "cursor", "cline", "codex", "opencode", "openclaw")

if ($Help) {
    Write-Host "Usage: .\install.bat [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Client <name[]>  Target client(s) - can be comma-separated or multiple -Client args"
    Write-Host "                    Supported: $($supportedClients -join ', ')"
    Write-Host "  -Help             Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\install.bat                    # Install to all clients"
    Write-Host "  .\install.bat -Client claude     # Install to Claude Desktop only"
    Write-Host "  .\install.bat -Client claude,cc  # Install to Claude Desktop and Claude Code"
    exit 0
}

Write-Host ""
Write-Host "======================================"
Write-Host "    Stata-MCP Installation Script"
Write-Host "======================================"
Write-Host ""

# Add common uv installation paths to PATH
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:USERPROFILE\.local\bin;$env:Path"

# Check if uv is installed
function Check-Uv {
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if ($null -ne $uv) {
        Write-Host "[OK] uv is installed" -ForegroundColor Green
        return $true
    }
    return $false
}

# Install uv
function Install-Uv {
    Write-Host "[!] uv is not installed" -ForegroundColor Yellow
    Write-Host ""

    $choice = Read-Host "Do you want to install uv? [Y/n]"
    switch -Regex ($choice) {
        "^(n|N|no|No|NO)$" {
            Write-Host "[X] Installation cancelled." -ForegroundColor Red
            exit 1
        }
        default {
            Write-Host ""
            $maxRetries = 3
            $retryCount = 0
            $installed = $false

            while ($retryCount -lt $maxRetries) {
                Write-Host "Installing uv... (attempt $($retryCount + 1)/$maxRetries)"
                try {
                    irm https://astral.sh/uv/install.ps1 | iex
                    $installed = $true
                    break
                } catch {
                    $retryCount++
                    if ($retryCount -lt $maxRetries) {
                        Write-Host "[!] Installation failed, retrying in 3 seconds..." -ForegroundColor Yellow
                        Start-Sleep -Seconds 3
                    } else {
                        Write-Host "[X] Failed to install uv after $maxRetries attempts." -ForegroundColor Red
                        Write-Host "    Please install it manually: irm https://astral.sh/uv/install.ps1 | iex"
                        exit 1
                    }
                }
            }

            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

            # Re-check if uv is now available
            if (Get-Command uv -ErrorAction SilentlyContinue) {
                Write-Host "[OK] uv installed successfully" -ForegroundColor Green
            } else {
                Write-Host "[X] Failed to install uv. Please install it manually:" -ForegroundColor Red
                Write-Host "    irm https://astral.sh/uv/install.ps1 | iex"
                exit 1
            }
        }
    }
}

# Main installation logic
# Step 1: Check and install uv
if (-not (Check-Uv)) {
    Install-Uv
}

# Step 2: Parse and validate clients
$targetClients = @()
foreach ($c in $Client) {
    # Split by comma in case of "claude,cc" format
    $splitClients = $c -split ","
    foreach ($sc in $splitClients) {
        $trimmed = $sc.Trim()
        if ($trimmed -in $supportedClients) {
            $targetClients += $trimmed
        } elseif ($trimmed -ne "") {
            Write-Host "[X] Unknown client: $trimmed" -ForegroundColor Red
            Write-Host "    Supported clients: $($supportedClients -join ', ')"
        }
    }
}

# Step 3: Install to clients
if ($targetClients.Count -eq 0) {
    # No specific clients specified, install to all
    Write-Host ""
    Write-Host "Installing to all supported clients..."
    uvx stata-mcp install --all
} else {
    # Install to specified clients
    foreach ($client in $targetClients) {
        Write-Host ""
        Write-Host "Installing to $client..."
        uvx stata-mcp install -c $client
    }
}

# Step 4: Remind user to restart
Write-Host ""
Write-Host "======================================"
Write-Host "[OK] Installation complete!" -ForegroundColor Green
Write-Host "======================================"
Write-Host ""
Write-Host "Please restart your MCP client(s) for the changes to take effect."
Write-Host ""
Write-Host "For more information, visit: https://github.com/sepinetam/stata-mcp"
Write-Host ""
