param([string]$PythonCommand = "python")

$ErrorActionPreference = "Stop"
$venv = Join-Path $PSScriptRoot ".venv"
$python = Join-Path $venv "Scripts/python.exe"
$requirements = Join-Path $PSScriptRoot "requirements.txt"

# 프로젝트 경로와 Python 명령을 사용해 가상환경을 만들고 실행 의존성을 설치한다.
if (-not (Test-Path $python)) {
    & $PythonCommand -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
}
& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

Write-Host "LUCID setup is complete."
Write-Host 'Run from the project folder: .\.venv\Scripts\python.exe main.py'
