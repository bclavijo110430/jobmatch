#!/bin/bash
# JobMatch entrypoint: start automation (if enabled) + FastAPI app

set -e

echo "=== JobMatch starting ==="

# Start automation in background if AUTO_START=true
if [ "${AUTO_START:-false}" = "true" ]; then
    echo "[entrypoint] Launching auto-starter in background..."
    python3 -m src.auto_starter &
fi

# Start FastAPI + static Astro UI
echo "[entrypoint] Launching FastAPI server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8501
