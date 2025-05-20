@echo off
REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run this script as Administrator!
    pause
    exit /b
)

REM Check if nssm command is available
where nssm >nul 2>&1
if errorlevel 1 (
    echo NSSM not found. Installing NSSM via winget...
    winget install nssm.nssm --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo Failed to install NSSM. Please install it manually.
        pause
        exit /b
    )
    echo NSSM installed successfully.
) else (
    echo NSSM found.
)

set SERVICE_NAME=DNSProxyService
set EXE_PATH=%~dp0main.exe

echo Installing %SERVICE_NAME% as a Windows service...

REM Install service using NSSM from PATH
nssm install %SERVICE_NAME% "%EXE_PATH%"

REM Set service to auto start
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Set service dependency on DNS Client (Dnscache)
sc config %SERVICE_NAME% depend= Dnscache

REM Start the service
net start %SERVICE_NAME%

echo %SERVICE_NAME% installed and started successfully.
pause
