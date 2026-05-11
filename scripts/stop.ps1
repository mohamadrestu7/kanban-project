# Project Management MVP - Stop Script for Windows

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
Set-Location ..

Write-Host "Stopping Project Management MVP..." -ForegroundColor Yellow
docker compose down

Write-Host "Containers stopped." -ForegroundColor Green
