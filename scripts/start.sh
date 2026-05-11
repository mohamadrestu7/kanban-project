#!/bin/bash

# Project Management MVP - Start Script for Mac/Linux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ".env file created. Please update with your OPENAI_API_KEY."
fi

# Check if Docker is running
echo "Checking Docker status..."
if ! docker ps > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build frontend
echo "Building frontend..."
cd frontend
if [ ! -x "node_modules/.bin/next" ]; then
    echo "Installing frontend dependencies..."
    npm ci
    if [ $? -ne 0 ]; then
        echo "Frontend dependency install failed. Check npm output above."
        exit 1
    fi
fi
npm run build
if [ $? -ne 0 ]; then
    echo "Frontend build failed. Check npm output above."
    exit 1
fi
cd ..

echo "Starting Project Management MVP..."
echo "Building Docker image..."
docker compose build

echo "Starting containers..."
docker compose up -d

# Wait for service to be ready
echo "Waiting for service to start..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/api/test > /dev/null 2>&1; then
        echo "Service is ready!"
        break
    fi
    attempt=$((attempt + 1))
    sleep 1
done

if [ $attempt -eq $max_attempts ]; then
    echo "Service failed to start. Check logs with: docker compose logs"
    exit 1
fi

echo ""
echo "=========================================="
echo "Project Management MVP is running!"
echo "=========================================="
echo ""
echo "Frontend: http://localhost:8000"
echo "API: http://localhost:8000/api/test"
echo ""
echo "To stop: Run ./scripts/stop.sh"
echo "To view logs: docker compose logs -f"
echo ""
