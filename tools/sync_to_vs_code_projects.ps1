# Sync this Gladiavore worktree to the preferred working directory.
# Run from the worktree root (or any cwd; script locates itself).
#
# Usage (PowerShell):
#   .\tools\sync_to_vs_code_projects.ps1
#   .\tools\sync_to_vs_code_projects.ps1 -WhatIf
#
# Default destination: C:\VS Code Projects\gladiavore
# Backs up existing destination to gladiavore_backup_YYYYMMDD_HHMMSS if it already has content.

param(
    [string]$Destination = "C:\VS Code Projects\gladiavore",
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"
$Source = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Write-Host "Source:      $Source"
Write-Host "Destination: $Destination"

if (-not (Test-Path $Destination)) {
    if ($WhatIf) {
        Write-Host "Would create $Destination"
    } else {
        New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    }
}

$destHasGit = Test-Path (Join-Path $Destination ".git")
$destHasSrc = Test-Path (Join-Path $Destination "src")
if ($destHasGit -or $destHasSrc) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backup = "${Destination}_backup_$stamp"
    Write-Host "Existing destination found; backup -> $backup"
    if (-not $WhatIf) {
        Copy-Item -Path $Destination -Destination $backup -Recurse -Force
    }
}

# Mirror product tree; exclude heavy/local noise
$excludeDirs = @(
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    "gladiavore.egg-info", "kds_vore_roguelike.egg-info",
    "dist", "build", "agent-tools", "terminals", "mcps"
)

$robolog = Join-Path $env:TEMP "gladiavore_sync_$([guid]::NewGuid().ToString('N')).log"
$xd = ($excludeDirs | ForEach-Object { "/XD"; $_ })
$args = @(
    $Source, $Destination,
    "/MIR", "/R:1", "/W:1", "/NFL", "/NDL", "/NP",
    "/XF", "*.pyc",
    "/LOG:$robolog"
) + $xd

if ($WhatIf) {
    Write-Host "Would run: robocopy $($args -join ' ')"
    exit 0
}

Write-Host "Running robocopy /MIR (see $robolog)..."
& robocopy @args
$code = $LASTEXITCODE
# robocopy: 0-7 success-ish
if ($code -ge 8) {
    throw "robocopy failed with exit code $code"
}

Write-Host "Sync complete (robocopy exit $code)."
Write-Host "Next:"
Write-Host "  cd `"$Destination`""
Write-Host "  pip uninstall kds-vore-roguelike -y"
Write-Host "  pip install -e `".[dev]`""
Write-Host "  python -m src.main"
