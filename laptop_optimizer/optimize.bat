@echo off
setlocal EnableDelayedExpansion
title Windows 11 Laptop Optimizer

:: Check for Administrative privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunScript
) else (
    echo [INFO] Administrative rights not detected.
    echo Requesting elevation for maximum system tuning (SSD TRIM, Services, etc.)...
    powershell -Command "Start-Process cmd -ArgumentList '/k \"\"%~f0\"\"' -Verb RunAs" 2>nul
    if %errorLevel% == 0 (
        exit /b
    ) else (
        echo Running with standard user permissions...
        goto :RunScript
    )
)

:RunScript
cls
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Optimize-Laptop.ps1"
if %errorLevel% neq 0 (
    echo.
    echo [NOTICE] Script exited with code %errorLevel%.
    pause
)
