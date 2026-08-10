Write-Host "Stopping container pm-app..." -ForegroundColor Yellow
docker stop pm-app 2>$null | Out-Null

Write-Host "Removing container pm-app..." -ForegroundColor Yellow
docker rm pm-app 2>$null | Out-Null

Write-Host "Container stopped and removed successfully." -ForegroundColor Green
