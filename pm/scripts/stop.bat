@echo off
echo Stopping container pm-app...
docker stop pm-app 2>nul

echo Removing container pm-app...
docker rm pm-app 2>nul

echo Container stopped and removed successfully.
