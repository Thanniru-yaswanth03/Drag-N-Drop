@echo off
echo Building Docker container pm-app...
docker build -t pm-app .

echo Stopping existing container if running...
docker stop pm-app 2>nul
docker rm pm-app 2>nul

echo Starting container pm-app on http://localhost:8000 ...
docker run -d --name pm-app -p 8000:8000 pm-app

echo Container started successfully!
echo Health check: http://localhost:8000/api/health
echo Application:  http://localhost:8000/
