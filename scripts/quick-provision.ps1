#Requires -Version 5.1
<#
.SYNOPSIS
  Fast provision — packages then runs ATK CLI (no OAuth prompts).
#>
param(
    [switch]$PackageOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$AgentRoot = Join-Path $Root "agent"

Write-Host "==> Fast provision path" -ForegroundColor Cyan
Write-Host "    (OAuth removed — no credential prompts)" -ForegroundColor Gray

& (Join-Path $PSScriptRoot "package-agent.ps1")
if ($LASTEXITCODE -ne 0) { exit 1 }

if ($PackageOnly) {
    Write-Host "[ok] Package-only mode — upload zip manually or use ATK Deploy." -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "==> Running ATK provision (CLI)..." -ForegroundColor Cyan
Write-Host "    First run may download CLI (~1 min). Subsequent runs are faster." -ForegroundColor Gray

Push-Location $AgentRoot
try {
    npx -y --package @microsoft/m365agentstoolkit-cli atk provision --env dev
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[warn] CLI provision failed or timed out." -ForegroundColor Yellow
        Write-Host "       Use manual sideload — zip is already built:" -ForegroundColor Yellow
        Write-Host "       agent\appPackage\build\appPackage.dev.zip" -ForegroundColor Yellow
        Write-Host "       https://dev.teams.microsoft.com/apps" -ForegroundColor Yellow
        exit 1
    }
    Write-Host ""
    Write-Host "[ok] Provision complete. Test at https://m365.cloud.microsoft/chat" -ForegroundColor Green
} finally {
    Pop-Location
}
