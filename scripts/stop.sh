#!/bin/bash

# Project Management MVP - Stop Script for Mac/Linux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "Stopping Project Management MVP..."
docker compose down

echo "Containers stopped."
