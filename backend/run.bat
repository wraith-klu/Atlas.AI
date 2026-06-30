@echo off
REM run.bat — Launch the AI Job Search Agent from Command Prompt (cmd.exe)
REM Usage: Double-click this file or run it from the project directory

set PYTHONPATH=%~dp0
cd /d "%~dp0"

echo.
echo =========================================
echo   AI Job Search Agent — Starting...
echo =========================================
echo.

python main.py

echo.
echo =========================================
echo   Run complete. Press any key to exit.
echo =========================================
pause
