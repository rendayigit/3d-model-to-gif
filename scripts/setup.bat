@echo off
REM =============================================================================
REM Model Preview Generator - Setup Script for Windows
REM =============================================================================
REM This script sets up the development environment for the project.
REM
REM Usage:
REM   scripts\setup.bat
REM
REM =============================================================================

echo ==========================================
echo   Model Preview Generator Setup
echo ==========================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip -q

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install development dependencies
echo Installing development dependencies...
pip install pytest black ruff mypy -q

echo.
echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo To activate the environment:
echo   .venv\Scripts\activate
echo.
echo To run the application:
echo   python main.py
echo.
