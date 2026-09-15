param(
    [string]$OutputName = "kds-vore-roguelike-win-alpha"
)

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Installing project and packaging tools..."
python -m pip install -e .
python -m pip install --upgrade build pyinstaller

Write-Host "Building Windows alpha release..."
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_alpha.ps1 -OutputName $OutputName

Write-Host "Release artifacts:"
Write-Host "- dist\kds-vore-roguelike\kds-vore-roguelike.exe"
Write-Host "- dist\$OutputName.zip"
