@echo off
REM Project Management MVP - Start Script for Windows (Batch)

setlocal enabledelayedexpansion
cd /d "%~dp0\.."

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo .env file created. Please update with your OPENAI_API_KEY.
)

REM Check if Docker is running
echo Checking Docker status...
docker ps >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Build frontend
echo Building frontend...
cd frontend
if not exist "node_modules\.bin\next.cmd" (
    echo Installing frontend dependencies...
    call npm ci
    if errorlevel 1 (
        echo Frontend dependency install failed. Check npm output above.
        pause
        exit /b 1
    )
)
call npm run build
if errorlevel 1 (
    echo Frontend build failed. Check npm output above.
    pause
    exit /b 1
)
cd ..

echo Starting Project Management MVP...
echo Building Docker image...
docker compose build

echo Starting containers...
docker compose up -d

REM Wait for service to be ready
echo Waiting for service to start...
setlocal enabledelayedexpansion
set "max_attempts=30"
set "attempt=0"

:wait_loop
if !attempt! geq !max_attempts! (
    echo Service failed to start. Check logs with: docker compose logs
    pause
    exit /b 1
)

timeout /t 1 /nobreak >nul 2>&1
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000/api/test' -UseBasicParsing -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }"
if !errorlevel! equ 0 (
    echo Service is ready!
    goto service_ready
)

set /a "attempt=!attempt!+1"
goto wait_loop

:service_ready
echo.
echo ==========================================
echo Project Management MVP is running!
echo ==========================================
echo.
echo Frontend: http://localhost:8000
echo API: http://localhost:8000/api/test
echo.
echo To stop: Run scripts\stop.bat
echo To view logs: docker compose logs -f
echo.
pause
