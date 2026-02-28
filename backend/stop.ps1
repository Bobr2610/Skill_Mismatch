# Stop DevMetrics backend (Flask on port 5000)
Write-Host "Stopping DevMetrics backend..." -ForegroundColor Yellow

$pids = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($pids) {
    $pids | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
    Write-Host "Stopped process(es) on port 5000." -ForegroundColor Green
} else {
    Write-Host "No process found on port 5000." -ForegroundColor Gray
}
