param(
    [string]$OutputName = "gladiavore-win-alpha"
)

$repo = Split-Path -Parent $PSScriptRoot
$dist = Join-Path $repo "dist"
$build = Join-Path $repo "build"
$packageDir = Join-Path $dist "gladiavore"
$archivePath = Join-Path $dist "$OutputName.zip"

Push-Location $repo
Remove-Item -Recurse -Force $dist, $build -ErrorAction SilentlyContinue

& .\.venv\Scripts\python.exe -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name "gladiavore" `
  --distpath $dist `
  --workpath $build `
  --add-data "data;data" `
  --add-data "README.md;." `
  "src\main.py"

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

if (-not (Test-Path $packageDir)) {
    throw "Expected package directory not found: $packageDir"
}

Copy-Item "README.md" $packageDir -Force
Copy-Item "data\Readme.txt" $packageDir -Force

if (Test-Path $archivePath) {
    Remove-Item $archivePath -Force
}

Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $archivePath -Force
Pop-Location

Write-Host "Built: $packageDir"
Write-Host "Archive: $archivePath"
