#!/bin/bash

echo ""
echo "========================================"
echo "      WMR GROUP APPS - LAUNCHER"
echo "========================================"
echo ""

PYTHON_CMD="python3"

if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
        echo "[*] Python3 not found, using python"
    else
        echo "ERROR: Python not found!"
        echo "Please install Python3 first:"
        echo "sudo apt-get install python3 python3-pip"
        exit 1
    fi
fi

echo "[*] Python version:"
$PYTHON_CMD --version

echo ""
echo "Application Manager Features:"
echo "- Manager updates from WMR-Group/WMR-GROUP-APPS"
echo "- App updates from their own GitHub repositories"
echo "- EXE/BAT file detection"
echo "- Black/white console-style UI"
echo "- Application installation/removal"
echo "- 7 applications available"
echo ""

echo "[*] Installing requirements..."
if [ -f "requirements.txt" ]; then
    $PYTHON_CMD -m pip install --upgrade pip
    $PYTHON_CMD -m pip install -r requirements.txt
else
    echo "WARNING: requirements.txt not found!"
    echo "Installing default dependencies..."
    $PYTHON_CMD -m pip install --upgrade pip
    $PYTHON_CMD -m pip install requests Pillow psutil tqdm colorama watchdog python-dateutil
fi

echo ""
echo "[*] Starting WMR Group Apps v1.0.2..."
echo ""

$PYTHON_CMD main.py

echo ""
read -p "Press Enter to continue..."