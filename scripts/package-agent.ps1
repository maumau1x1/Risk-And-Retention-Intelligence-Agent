#Requires -Version 5.1
<#
.SYNOPSIS
  Build a sideload-ready app package zip WITHOUT waiting for ATK Provision.
.DESCRIPTION
  Substitutes env vars, copies appPackage files, creates appPackage/build/appPackage.dev.zip
  Upload this zip manually at https://dev.teams.microsoft.com if CLI provision fails.
#>
param(
    [string]$EnvName = "dev"
)

$ErrorActionPreference = "Stop"
$AgentRoot = Join-Path (Split-Path -Parent $PSScriptRoot) "agent"
$AppPackage = Join-Path $AgentRoot "appPackage"
$BuildDir = Join-Path $AppPackage "build"
$StagingDir = Join-Path $BuildDir "staging"
$ZipPath = Join-Path $BuildDir "appPackage.$EnvName.zip"

function Read-EnvFile {
    param([string]$Path)
    $vars = @{}
    if (-not (Test-Path $Path)) { return $vars }
    Get-Content $Path | ForEach-Object {
        if ($_ -match '^\s*([^#=][^=]*?)=(.*)$') {
            $vars[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    return $vars
}

function Substitute-Vars {
    param([string]$Text, [hashtable]$Vars)
    foreach ($key in $Vars.Keys) {
        $Text = $Text -replace [regex]::Escape('${{' + $key + '}}'), $Vars[$key]
    }
    return $Text
}

Write-Host "==> Packaging agent (fast path)" -ForegroundColor Cyan

$vars = @{}
foreach ($file in @(".env.$EnvName", ".env.$EnvName.user")) {
    $path = Join-Path (Join-Path $AgentRoot "env") $file
    foreach ($kv in (Read-EnvFile $path).GetEnumerator()) {
        $vars[$kv.Key] = $kv.Value
    }
}

if (-not $vars["TEAMS_APP_ID"]) {
    $vars["TEAMS_APP_ID"] = [guid]::NewGuid().ToString()
    Write-Host "[warn] No TEAMS_APP_ID in env - generated: $($vars['TEAMS_APP_ID'])" -ForegroundColor Yellow
    Write-Host "       Add to agent/env/.env.dev if you already provisioned once." -ForegroundColor Yellow
}
if (-not $vars["APP_NAME_SUFFIX"]) { $vars["APP_NAME_SUFFIX"] = "-dev" }
if (-not $vars["MCP_SERVER_URL"]) {
    throw "MCP_SERVER_URL not set. Add your ngrok URL to agent/env/.env.dev.user"
}

Write-Host "  TEAMS_APP_ID:    $($vars['TEAMS_APP_ID'])"
Write-Host "  MCP_SERVER_URL:  $($vars['MCP_SERVER_URL'])"

if (Test-Path $StagingDir) { Remove-Item $StagingDir -Recurse -Force }
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null

$jsonFiles = @(
    "manifest.json",
    "declarativeAgent.json",
    "risk-retention-plugin.json"
)
foreach ($name in $jsonFiles) {
    $src = Join-Path $AppPackage $name
    if (-not (Test-Path $src)) { throw "Missing $name" }
    $content = Get-Content $src -Raw -Encoding UTF8
    $content = Substitute-Vars -Text $content -Vars $vars
    Set-Content -Path (Join-Path $StagingDir $name) -Value $content -Encoding UTF8 -NoNewline
}

Copy-Item (Join-Path $AppPackage "color.png") $StagingDir
Copy-Item (Join-Path $AppPackage "outline.png") $StagingDir

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
Compress-Archive -Path (Join-Path $StagingDir "*") -DestinationPath $ZipPath -Force

Write-Host ""
Write-Host "[ok] Package ready:" -ForegroundColor Green
Write-Host "     $ZipPath"
Write-Host ""
Write-Host "Manual sideload (if ATK Provision hangs):" -ForegroundColor Cyan
Write-Host "  1. Open https://dev.teams.microsoft.com/apps"
Write-Host "  2. Import app and select the zip above"
Write-Host "  3. Preview in Teams, then test in https://m365.cloud.microsoft/chat"
Write-Host ""
Write-Host "Or run: .\scripts\quick-provision.ps1" -ForegroundColor Cyan
