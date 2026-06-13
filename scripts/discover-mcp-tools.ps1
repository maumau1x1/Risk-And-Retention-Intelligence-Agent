#Requires -Version 5.1
<#
.SYNOPSIS
  Discover MCP tools from the running server (for syncing ai-plugin.json).
.PARAMETER McpUrl
  MCP server URL, e.g. http://localhost:8080/mcp
#>
param(
    [string]$McpUrl = "http://localhost:8080/mcp"
)

$ErrorActionPreference = "Stop"
$headers = @{
    "Content-Type"  = "application/json"
    "Accept"        = "application/json, text/event-stream"
}

Write-Host "==> MCP tool discovery: $McpUrl" -ForegroundColor Cyan

$initBody = @{
    jsonrpc = "2.0"
    id      = 1
    method  = "initialize"
    params  = @{
        protocolVersion = "2025-06-18"
        capabilities    = @{}
        clientInfo      = @{ name = "risk-agent-setup"; version = "1.0.0" }
    }
} | ConvertTo-Json -Depth 10

$initResponse = Invoke-WebRequest -Uri $McpUrl -Method POST -Headers $headers -Body $initBody -UseBasicParsing
$sessionId = $initResponse.Headers["mcp-session-id"]
if (-not $sessionId) {
    throw "No mcp-session-id header returned. Is the MCP server running?"
}

$notifyHeaders = $headers.Clone()
$notifyHeaders["mcp-session-id"] = $sessionId
$notifyBody = '{"jsonrpc":"2.0","method":"notifications/initialized"}'
Invoke-WebRequest -Uri $McpUrl -Method POST -Headers $notifyHeaders -Body $notifyBody -UseBasicParsing | Out-Null

$listBody = '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
$listResponse = Invoke-WebRequest -Uri $McpUrl -Method POST -Headers $notifyHeaders -Body $listBody -UseBasicParsing
$payload = $listResponse.Content | ConvertFrom-Json
$tools = $payload.result.tools

$outPath = Join-Path (Split-Path -Parent $PSScriptRoot) "agent\appPackage\discovered-tools.json"
$tools | ConvertTo-Json -Depth 20 | Set-Content -Path $outPath -Encoding UTF8

Write-Host "[ok] Discovered $($tools.Count) tools -> $outPath" -ForegroundColor Green
$tools | ForEach-Object { Write-Host "  - $($_.name)" }
