#!/bin/bash
# JobMatch entrypoint: start automation (if enabled) + Streamlit app

echo "=== JobMatch starting ==="

# Start automation in background if AUTO_START=true
if [ "${AUTO_START:-false}" = "true" ]; then
    echo "[entrypoint] Launching auto-starter in background..."
    python3 -m src.auto_starter &
fi

# Start Streamlit app
echo "[entrypoint] Launching Streamlit..."
exec streamlit run app.py --server.address 0.0.0.0