#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
trap 'kill 0' EXIT

echo "Starting API on http://localhost:8000 ..."
cd "$ROOT"
uvicorn api.main:app --reload --port 8000 &

echo "Starting frontend on http://localhost:5173 ..."
cd "$ROOT/frontend"
npm run dev
