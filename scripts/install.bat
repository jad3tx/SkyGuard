@echo off
REM SkyGuard Installation Script for Windows
REM Automated installation for the SkyGuard raptor alert system

setlocal enabledelayedexpansion

echo [INFO] Starting SkyGuard installation for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [INFO] Python found, checking version...
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.8+ is required
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "setup.py" (
    echo [ERROR] Please run this script from the SkyGuard root directory
    pause
    exit /b 1
)

if not exist "skyguard" (
    echo [ERROR] SkyGuard source directory not found
    pause
    exit /b 1
)

echo [INFO] Creating virtual environment...
if exist "venv" (
    echo [WARNING] Virtual environment already exists, removing...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [INFO] Installing Python packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements
    pause
    exit /b 1
)

echo [INFO] Installing SkyGuard...
pip install -e .
if errorlevel 1 (
    echo [ERROR] Failed to install SkyGuard
    pause
    exit /b 1
)

echo [INFO] Testing installation...
python -c "import skyguard; print('SkyGuard import successful')"
if errorlevel 1 (
    echo [ERROR] SkyGuard import failed
    pause
    exit /b 1
)

echo [INFO] Testing camera...
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera test: OK' if cap.isOpened() else 'Camera test: No camera detected'); cap.release()"

echo [SUCCESS] SkyGuard installation completed successfully!
echo.
echo Next steps:
echo 1. Configure SkyGuard: skyguard-setup
echo 2. Test the system: skyguard --test-system
echo 3. Start SkyGuard: skyguard
echo.
echo Note: Make sure to activate the virtual environment before running SkyGuard:
echo    venv\Scripts\activate.bat
echo.

pause
