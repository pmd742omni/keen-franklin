@echo off
title Laptop Hardware Optimizer City - Living System Dashboard
cd /d "%~dp0\.."

echo =================================================================
echo        LAPTOP HARDWARE OPTIMIZER CITY - AUTONOMOUS SWARM
echo   Native Windows 11 Tuning, Memory Compaction ^& Real-Time Visualizer
echo =================================================================
echo.
echo [1/2] Checking Python environment...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

echo [2/2] Launching Optimizer City Server on http://localhost:8000 ...
start "" "http://localhost:8000"

python -m uvicorn agent_city.server:app --host 127.0.0.1 --port 8000
if %errorLevel% neq 0 (
    echo.
    echo Server stopped.
    pause
)
