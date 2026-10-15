@echo off
setlocal
cd /d "%~dp0"
python build_installer.py
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
)
