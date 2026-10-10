@echo off
title Restore Previous Laptop Settings
cd /d "%~dp0"
echo =================================================================
echo         RESTORING ORIGINAL LAPTOP CONFIGURATION
echo =================================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Optimize-Laptop.ps1" -Preset Restore
echo.
echo Press any key to close...
pause >nul
