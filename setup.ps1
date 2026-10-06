param(
    [string]$PythonCommand = "python"
)

$ErrorActionPreference = "Stop"

& $PythonCommand --version

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $PythonCommand -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements-portable.txt

Write-Host ""
Write-Host "LUCID setup is complete."
Write-Host "Run: .\.venv\Scripts\Activate.ps1"
Write-Host "Then: python main.py"
