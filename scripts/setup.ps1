#Requires -Version 5.1
<#
.SYNOPSIS
  Bootstrap the Risk & Retention Intelligence Agent hackathon project.
.DESCRIPTION
  Installs Python MCP server dependencies, Node.js ATK CLI, and copies env templates.
#>
param(
    [switch]$SkipNode,
    [switch]$SkipPython
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host '==> Risk and Retention Intelligence Agent - Setup' -ForegroundColor Cyan
Write-Host "    Root: $Root"

# --- Environment files ---
if (-not (Test-Path "$Root\.env")) {
    Copy-Item "$Root\.env.example" "$Root\.env"
    Write-Host '[ok] Created .env from template - fill in your tenant values.' -ForegroundColor Green
}

$agentEnvDir = "$Root\agent\env"
if (-not (Test-Path $agentEnvDir)) {
    New-Item -ItemType Directory -Path $agentEnvDir -Force | Out-Null
}
foreach ($name in @(".env.dev", ".env.dev.user")) {
    $target = Join-Path $agentEnvDir $name
    if (-not (Test-Path $target)) {
        if ($name -eq ".env.dev") {
            @"
# ATK environment — populated by 'atk provision'
TEAMSFX_ENV=dev
APP_NAME_SUFFIX=-dev
MCP_SERVER_URL=http://localhost:8080/mcp
"@ | Set-Content -Path $target -Encoding UTF8
        } else {
            @"
# Local overrides (not committed)
MCP_SERVER_URL=http://localhost:8080/mcp
"@ | Set-Content -Path $target -Encoding UTF8
        }
        Write-Host "[ok] Created agent/env/$name" -ForegroundColor Green
    }
}

# --- Python MCP server ---
if (-not $SkipPython) {
    $mcpDir = "$Root\mcp-server"
    Push-Location $mcpDir
    try {
        if (-not (Test-Path ".venv")) {
            Write-Host "==> Creating Python virtual environment..." -ForegroundColor Yellow
            python -m venv .venv
        }
        & ".\.venv\Scripts\Activate.ps1"
        python -m pip install --upgrade pip
        pip install -e ".[dev,apps]"
        if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
        if (-not (Test-Path ".env")) {
            Copy-Item ".env.example" ".env"
            Write-Host "[ok] Created mcp-server/.env" -ForegroundColor Green
        }
        Write-Host "[ok] Python dependencies installed." -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

# --- Node.js ATK CLI ---
if (-not $SkipNode) {
    Write-Host "==> Verifying Microsoft 365 Agents Toolkit CLI..." -ForegroundColor Yellow
    $atkVersion = npx -y --package @microsoft/m365agentstoolkit-cli atk --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[ok] ATK CLI: $atkVersion" -ForegroundColor Green
    } else {
        Write-Host "[warn] ATK CLI check failed. Install VS Code extension 'Microsoft 365 Agents Toolkit'." -ForegroundColor Yellow
    }
}

# --- App package icons (required for provision) ---
$iconDir = "$Root\agent\appPackage"
$colorIcon = Join-Path $iconDir "color.png"
$outlineIcon = Join-Path $iconDir "outline.png"
if (-not ((Test-Path $colorIcon) -and (Test-Path $outlineIcon))) {
    Write-Host "[warn] Add color.png (192x192) and outline.png (32x32) to agent/appPackage/ before provisioning." -ForegroundColor Yellow
    Write-Host "       ATK 'Create Declarative Agent' scaffolds these automatically if you prefer." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Fill in .env and mcp-server/.env with Entra + Fabric IQ values"
Write-Host "  2. Run:  .\scripts\dev.ps1"
Write-Host "  3. In VS Code: ATK > Provision (agent/) after MCP server is reachable"
Write-Host "  4. Test at https://m365.cloud.microsoft/chat"
