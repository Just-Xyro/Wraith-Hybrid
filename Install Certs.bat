@echo off
title Install Mitmproxy Certificate
color 0b
cls

echo ====================================
echo Install Mitmproxy Certificate
echo ====================================
echo.

set CERT_PATH=%USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.cer

if not exist "%CERT_PATH%" (
    echo [ERROR] Certificate file not found at:
    echo %CERT_PATH%
    echo.
    echo Please run the application first to generate the certificate,
    echo or ensure mitmproxy is installed and has generated its CA certificate.
    echo.
    pause
    exit /b 1
)

echo [INFO] Found certificate at:
echo %CERT_PATH%
echo.

echo [SETUP] Installing certificate to Windows Root store...
echo.

certutil.exe -f -addstore Root "%CERT_PATH%"

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Certificate installed successfully!
    echo.
    echo The mitmproxy CA certificate has been added to the Trusted Root
    echo Certification Authorities store on your system.
) else (
    echo.
    echo [ERROR] Failed to install certificate.
    echo Please run this batch file as Administrator.
    echo.
)

echo.
pause
