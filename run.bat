@echo off
setlocal
cd /d "%~dp0"
echo Starting JADS Offline...
python main.py
if errorlevel 1 (
    echo.
    echo Application failed to start.
    pause
)
