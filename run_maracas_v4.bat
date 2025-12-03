@echo off
title MARACAS Pro v4.0 Launcher
color 1F

:: -----------------------------------------------------
:: MARACAS Pro v4.0 - Automated Launcher
:: Checks for Python, sets up environment, runs app.
:: -----------------------------------------------------

echo.
echo  =======================================================
echo   MARACAS Pro v4.0 -- Integrated Digital Heritage Mgmt
echo  =======================================================
echo.

:: 1. CHECK FOR PYTHON
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 4F
    echo [ERROR] Python was not found on this computer.
    echo.
    echo Please install Python 3.10 or higher from python.org.
    echo IMPORTANT: Check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

:: 2. SETUP VIRTUAL ENVIRONMENT (If not exists)
if not exist "venv" (
    echo [SETUP] First run detected. Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Could not create virtual environment.
        pause
        exit /b
    )
    echo [SETUP] Environment created.
) else (
    echo [INFO] Virtual environment found.
)

:: 3. ACTIVATE ENVIRONMENT
call venv\Scripts\activate.bat

:: 4. INSTALL/UPDATE DEPENDENCIES
echo [INFO] Checking and installing dependencies...
:: We install specifically what v4 needs. 
:: 'pip install' skips automatically if already installed.
pip install requests pandas keyring urllib3 tk >nul 2>&1

:: 5. LAUNCH APPLICATION
echo.
echo [START] Launching MARACAS Pro v4.0...
echo         Keep this black window open while the app is running.
echo.

python maracas_pro_v4.py

:: 6. EXIT HANDLING
if %errorlevel% neq 0 (
    color 4F
    echo.
    echo [ERROR] The application closed unexpectedly.
    echo         Read the error message above (if any).
    pause
) else (
    echo.
    echo [INFO] Application closed successfully.
)

deactivate