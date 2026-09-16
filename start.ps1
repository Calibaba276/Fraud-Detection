param([int]$FrontendPort = 3000)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Create .venv and install the Python dependencies first. See README.md.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend/node_modules'))) { throw 'Run npm install in frontend first. See README.md.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'artifacts/model.joblib'))) { throw 'Train the model first. See README.md.' }
if (-not $env:DATABASE_URL) { $env:DATABASE_URL = 'sqlite:///fraud_detection.db' }
if (-not $env:FRAUD_ALLOWED_ORIGINS) { $env:FRAUD_ALLOWED_ORIGINS = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort" }
$logDirectory = Join-Path $projectRoot 'artifacts'
$backendProcess = Start-Process -FilePath $projectPython -ArgumentList '-m','uvicorn','fraud_detection.api:app','--host','127.0.0.1','--port','8000','--workers','1' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory 'backend-output.log') -RedirectStandardError (Join-Path $logDirectory 'backend-error.log')
try {
    Start-Sleep -Seconds 2
    if ($backendProcess.HasExited) { throw 'The backend could not start. Check artifacts/backend-error.log. Another server may already be using port 8000.' }
    Write-Host "Sentinel dashboard: http://localhost:$FrontendPort"
    Write-Host 'Press Ctrl+C to stop. Backend logs are in artifacts.'
    Push-Location (Join-Path $projectRoot 'frontend')
    try { & npm.cmd run dev -- --host 127.0.0.1 --port $FrontendPort } finally { Pop-Location }
} finally {
    if (-not $backendProcess.HasExited) { Stop-Process -Id $backendProcess.Id }
}
