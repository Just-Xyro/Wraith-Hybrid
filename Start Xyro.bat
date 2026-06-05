@echo off
cd /d "%~dp0"
title Xyro
color 0b
cls

echo ====================================
echo Xyro Setup and Launcher
echo ====================================
echo.

echo [UPDATE] Checking for updates...
echo.

if not exist "version.json" (
    echo [INFO] version.json not found, creating default...
    echo {"version":"1.0.0","repo":"Just-Xyro/Xyro-Hybrid"} > version.json
)

for /f "tokens=2 delims=:," %%a in ('findstr "version" version.json') do set CURRENT_VERSION=%%a
set CURRENT_VERSION=%CURRENT_VERSION:"=%
set CURRENT_VERSION=%CURRENT_VERSION: =%

echo [INFO] Current version: %CURRENT_VERSION%

curl -s https://api.github.com/repos/Just-Xyro/Xyro-Hybrid/releases/latest > latest_release.json 2>nul

findstr "Not Found" latest_release.json >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Repository or release not found. Continuing with current version.
    goto :skip_update
)

if %errorlevel% neq 0 (
    echo [WARNING] Failed to check for updates. Continuing with current version.
    goto :skip_update
)

for /f "tokens=2 delims=:," %%a in ('findstr "tag_name" latest_release.json') do set LATEST_VERSION=%%a
set LATEST_VERSION=%LATEST_VERSION:"=%
set LATEST_VERSION=%LATEST_VERSION: =%

echo [INFO] Latest version: %LATEST_VERSION%

if "%LATEST_VERSION%"=="%CURRENT_VERSION%" (
    echo [UPDATE] Already up to date!
) else (
    echo [UPDATE] New version available: %LATEST_VERSION%
    echo [UPDATE] Updating...

    for /f "tokens=2 delims=:," %%a in ('findstr "browser_download_url" latest_release.json ^| findstr ".zip"') do set DOWNLOAD_URL=%%a
    set DOWNLOAD_URL=%DOWNLOAD_URL:"=%
    set DOWNLOAD_URL=%DOWNLOAD_URL: =%

    curl -L -o Xyro_Update.zip "%DOWNLOAD_URL%"

    if %errorlevel% neq 0 (
        echo [WARNING] Failed to download update. Continuing with current version.
        goto :skip_update
    )

    echo [UPDATE] Extracting update...
    tar -xf Xyro_Update.zip

    for /d %%d in (Xyro-*) do (
        xcopy "%%d\*" . /Y /E /I /H
        rmdir /s /q "%%d"
    )

    echo {"version":"%LATEST_VERSION%","repo":"Just-Xyro/Xyro-Hybrid"} > version.json

    del Xyro_Update.zip
    del latest_release.json

    echo [SUCCESS] Update complete! New version: %LATEST_VERSION%
)

:skip_update
del latest_release.json 2>nul
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Python is not installed. Attempting to install...
    echo.
    
    winget install --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements -e --silent
    if %errorlevel% neq 0 (
        echo.
        echo [WARNING] winget installation may have encountered issues.
        echo Verifying Python installation...
    )
    
    echo.
    echo [INFO] Waiting for Python installation to complete...
    timeout /t 5 /nobreak >nul
    
    echo Refreshing environment variables...
    call refreshenv >nul 2>&1
    if %errorlevel% neq 0 (
        echo [INFO] refreshenv not available, using alternative method...
        for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "PATH=%%b"
        for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "PATH=%%b;%PATH%"
    )
    timeout /t 3 /nobreak >nul
    
    echo.
    echo [VERIFY] Checking if Python is now available...
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Python installation verification failed.
        echo Please install Python manually from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
    echo [SUCCESS] Python installed and verified successfully!
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
