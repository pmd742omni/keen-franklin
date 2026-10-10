@echo off
chcp 65001 >nul
title Laptop Optimizer Metropolis - Command Center
cd /d "%~dp0"
python start.py
if %errorLevel% neq 0 (
    echo.
    echo Press any key to exit...
    pause >nul
)
