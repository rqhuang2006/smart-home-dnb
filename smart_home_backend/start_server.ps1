$port = 8000
$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" } | Select-Object -First 1
if ($connection) {
    $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
    Write-Host "Port $port is already in use by PID $($connection.OwningProcess) $($process.ProcessName)." -ForegroundColor Yellow
    Write-Host "Stop that process first, or run: Stop-Process -Id $($connection.OwningProcess)" -ForegroundColor Yellow
    exit 1
}
uvicorn main:app --host 0.0.0.0 --port $port
