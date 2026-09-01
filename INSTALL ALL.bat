@echo off
title Install WRAITH Requirements
color 0B
cls

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo ====================================
echo INSTALL WRAITHE REQUIREMENTS  
echo ====================================
echo.

echo [STEP 1/3] Installing Python packages...
echo.

echo Installing pywebview...
python -m pip install pywebview
if errorlevel 1 (
    echo [ERROR] Failed to install pywebview.
    pause
    exit /b 1
)

echo Installing mitmproxy...
python -m pip install mitmproxy
if errorlevel 1 (
    echo [ERROR] Failed to install mitmproxy.
    pause
    exit /b 1
)

echo Installing psutil...
python -m pip install psutil
if errorlevel 1 (
    echo [ERROR] Failed to install psutil.
    pause
    exit /b 1
)

echo Installing cryptography...
python -m pip install cryptography
if errorlevel 1 (
    echo [ERROR] Failed to install cryptography.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Python packages installed successfully!
echo.

echo ====================================
echo [STEP 2/3] Installing Mitmproxy Certificate
echo ====================================
echo.

set "CERT_PATH=%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.cer"

if not exist "%CERT_PATH%" (
    echo [WARNING] Certificate file not found:
    echo.
    echo %CERT_PATH%
    echo.
    echo Run the application once to generate the certificate,
    echo then run this installer again.
    echo.
    pause
    exit /b 1
)

echo [INFO] Found certificate:
echo %CERT_PATH%
echo.

echo Installing certificate to Windows Trusted Root store...
echo.

certutil -f -addstore Root "%CERT_PATH%"

set "CERT_RESULT=%ERRORLEVEL%"

echo.

if NOT "%CERT_RESULT%"=="0" (
    echo [ERROR] Failed to install certificate.
    echo.
    echo Make sure this script is running as Administrator.
    echo.
    pause
    exit /b 1
)

echo [SUCCESS] Certificate installed successfully!
echo.

echo ====================================
echo [STEP 3/3] Generating All Logos
echo ====================================
echo.

if not exist "generate_all_logos.py" (
    echo [WARNING] generate_all_logos.py not found.
    echo.
    echo Skipping logo generation.
    echo.
) else (
    echo Running logo generation script...
    echo.
    python generate_all_logos.py --force
    
    if errorlevel 1 (
        echo.
        echo [WARNING] Logo generation encountered some errors.
        echo.
        echo This is not critical - the application will still work.
        echo.
    ) else (
        echo.
        echo [SUCCESS] Logos generated successfully!
        echo.
    )
)

echo ====================================
echo WRAITH INSTALLATION COMPLETE!
echo ====================================
echo.
echo You can now run WRAITH using RUN.bat
echo.

pause
