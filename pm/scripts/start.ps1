Write-Host "Building Docker container pm-app..." -ForegroundColor Cyan
docker build -t pm-app .

Write-Host "Stopping existing container if running..." -ForegroundColor Yellow
docker stop pm-app 2>$null | Out-Null
docker rm pm-app 2>$null | Out-Null

Write-Host "Starting container pm-app on http://localhost:8000 ..." -ForegroundColor Cyan
if (Test-Path .env) {
    docker run -d --name pm-app --env-file .env -p 8000:8000 pm-app | Out-Null
} else {
    docker run -d --name pm-app -p 8000:8000 pm-app | Out-Null
}

Write-Host "Container started successfully!" -ForegroundColor Green
Write-Host "Health check: http://localhost:8000/api/health"
Write-Host "Application:  http://localhost:8000/"
