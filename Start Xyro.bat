@echo off
cd /d "%~dp0"
title Xyro
color 0b
cls

echo ====================================
echo Xyro Setup and Launcher
echo ====================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Python is not installed. Attempting to install...
    echo.
    
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install Python using winget.
        echo Please install Python manually from https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo [SUCCESS] Python installed successfully!
    echo.
    echo Refreshing environment variables...
    refreshenv >nul 2>&1
    timeout /t 3 /nobreak >nul
) else (
    echo [CHECK] Python is already installed.
)

echo.
echo [INFO] Python version:
python --version
echo.

echo [CHECK] Verifying Python packages...
pip show cryptography >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Installing Python packages...
    echo.
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Failed to install requirements. Please check your internet connection.
        pause
        exit /b 1
    )
    echo.
    echo [SUCCESS] All packages installed successfully!
) else (
    echo [CHECK] All packages are already installed.
)

echo.
echo ====================================
echo Starting Xyro...
echo ====================================
echo.
python main.py
pause
