#!/usr/bin/env bash
# Jerry – Powertech Analysis Tools
# One-shot setup: installs all Python and Node dependencies
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing Python dependencies ==="
pip install -r "$ROOT/requirements.txt"
pip install -r "$ROOT/api/requirements-api.txt"

echo ""
echo "=== Installing Node dependencies ==="
cd "$ROOT/frontend"
npm install

echo ""
echo "=== Setup complete ==="
echo ""
echo "To run the app:"
echo "  Terminal 1 (API):      cd $ROOT && uvicorn api.main:app --reload --port 8000"
echo "  Terminal 2 (Frontend): cd $ROOT/frontend && npm run dev"
echo ""
echo "Then open: http://localhost:5173"
