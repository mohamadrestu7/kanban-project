@echo off
REM Project Management MVP - Stop Script for Windows (Batch)

cd /d "%~dp0\.."

echo Stopping Project Management MVP...
docker compose down

echo Containers stopped.
pause
