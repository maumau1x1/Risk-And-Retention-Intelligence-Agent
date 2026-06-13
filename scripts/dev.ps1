#Requires -Version 5.1
<#
.SYNOPSIS
  Start the Python MCP server in development mode with hot reload.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$McpDir = Join-Path $Root "mcp-server"

# Load root .env if present (simple key=value parser)
$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

$port = if ($env:MCP_SERVER_PORT) { $env:MCP_SERVER_PORT } else { "8080" }
Write-Host "==> Starting MCP server on port $port" -ForegroundColor Cyan
Write-Host "    Local endpoint: http://localhost:$port/mcp"
Write-Host "    Expose publicly with: ngrok http $port" -ForegroundColor Yellow

Push-Location $McpDir
try {
    & ".\.venv\Scripts\Activate.ps1"
    $env:PYTHONPATH = "src"
    python -m risk_agent_mcp.main
} finally {
    Pop-Location
}
