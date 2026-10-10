#!/usr/bin/env bash
# Agent Metropolis — Unix Quick-Start Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================="
echo "            AGENT METROPOLIS - VIRTUAL CITY SIMULATION"
echo "================================================================="
echo ""
echo "[*] Launching Agent Metropolis FastAPI Server on http://localhost:8000 ..."

# Attempt to open browser
if command -v xdg-open > /dev/null; then
  xdg-open "http://localhost:8000" &
elif command -v open > /dev/null; then
  open "http://localhost:8000" &
fi

python3 -m uvicorn agent_city.server:app --host 0.0.0.0 --port 8000 --reload
