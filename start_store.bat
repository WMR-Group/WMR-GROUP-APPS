@echo off
chcp 65001 >nul
title WMR Group Apps - Launcher
color 07

echo ========================================
echo      WMR GROUP APPS - LAUNCHER
echo ========================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

echo [*] Starting WMR Group Apps v1.0.1...
echo.
echo Application Manager Features:
echo - GitHub update checking
echo - EXE/BAT file detection
echo - Black/white console-style UI
echo - Application installation/removal
echo - 7 applications available
echo.
pip install -r requirements.txt
python main.py

pause