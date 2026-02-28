# Start DevMetrics backend
Set-Location $PSScriptRoot

Write-Host "Starting DevMetrics backend..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet
Write-Host "Open http://localhost:5000" -ForegroundColor Green
python app.py
