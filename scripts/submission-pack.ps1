#Requires -Version 5.1
<#
.SYNOPSIS
  Create hackathon submission zip (excludes .venv, node_modules, secrets).
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$OutZip = Join-Path $Root "Risk-Retention-Agent-submission.zip"
$Staging = Join-Path $env:TEMP "risk-agent-submission"

Write-Host "==> Building submission package" -ForegroundColor Cyan

if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
New-Item -ItemType Directory -Path $Staging -Force | Out-Null

$exclude = @('.venv', 'node_modules', '.pytest_cache', '__pycache__', '.git', 'build', '.env', '.mcp-auth')
Get-ChildItem $Root -Force | Where-Object {
    $_.Name -notin $exclude -and $_.Name -ne 'Risk-Retention-Agent-submission.zip'
} | ForEach-Object {
    Copy-Item $_.FullName -Destination $Staging -Recurse -Force -ErrorAction SilentlyContinue
}

# Ensure package zip exists for judges
& (Join-Path $PSScriptRoot "package-agent.ps1") -ErrorAction SilentlyContinue

if (Test-Path $OutZip) { Remove-Item $OutZip -Force }
Compress-Archive -Path (Join-Path $Staging "*") -DestinationPath $OutZip -Force
Remove-Item $Staging -Recurse -Force

Write-Host "[ok] Submission zip: $OutZip" -ForegroundColor Green
Write-Host "     Upload this to your hackathon portal." -ForegroundColor Gray
