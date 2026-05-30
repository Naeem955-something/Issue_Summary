@echo off
cd /d "%~dp0"
echo.
echo ============================================================
echo LEAN MVP - Testing Backend Setup
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run test
python test_setup.py

pause
