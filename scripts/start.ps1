# Project Management MVP - Start Script for Windows

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
Set-Location ..

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ".env file created. Please update with your OPENAI_API_KEY." -ForegroundColor Yellow
}

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Cyan
$DockerCheck = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Cyan
Set-Location frontend
if (-not (Test-Path "node_modules/.bin/next.cmd") -and -not (Test-Path "node_modules/.bin/next")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    npm ci
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Frontend dependency install failed. Check npm output above." -ForegroundColor Red
        exit 1
    }
}
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed. Check npm output above." -ForegroundColor Red
    exit 1
}
Set-Location ..

Write-Host "Starting Project Management MVP..." -ForegroundColor Green
Write-Host "Building Docker image..." -ForegroundColor Cyan
docker compose build

Write-Host "Starting containers..." -ForegroundColor Cyan
docker compose up -d

# Wait for service to be ready
Write-Host "Waiting for service to start..." -ForegroundColor Cyan
$maxAttempts = 30
$attempt = 0
do {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/test" -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "Service is ready!" -ForegroundColor Green
            break
        }
    } catch {
        $attempt++
        if ($attempt -lt $maxAttempts) {
            Start-Sleep -Seconds 1
        }
    }
} while ($attempt -lt $maxAttempts)

if ($attempt -eq $maxAttempts) {
    Write-Host "Service failed to start. Check logs with: docker compose logs" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Project Management MVP is running!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API: http://localhost:8000/api/test" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop: Run ./stop.ps1" -ForegroundColor Yellow
Write-Host "To view logs: docker compose logs -f" -ForegroundColor Yellow
Write-Host ""
