@echo off
chcp 65001 >nul
title Build WMR Group Apps EXE
color 07

echo ========================================
echo    BUILDING WMR GROUP APPS EXE
echo ========================================
echo.

echo [*] Installing PyInstaller...
python -m pip install pyinstaller

echo.
echo [*] Building executable...
pyinstaller --onefile --windowed ^
  --name "WMR_Group_Apps" ^
  --icon=icon.ico ^
  --add-data "*.json;." ^
  --hidden-import=requests ^
  --hidden-import=PIL ^
  --hidden-import=tkinter ^
  app_store.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [✓] Build successful!
echo.
echo Executable location: dist\WMR_Group_Apps.exe
echo.
echo You can now:
echo 1. Copy WMR_Group_Apps.exe to main folder
echo 2. Run install.bat to setup directories
echo 3. Use start_store.bat to launch
echo.
pause