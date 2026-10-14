@echo off
title CODS - Inno Setup Compiler Helper
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================================
echo    CODS - Inno Setup Build Automation
echo ======================================================================
echo.

set "ISCC_PATH="

REM Check PATH
where iscc >nul 2>nul
if %errorlevel% equ 0 (
    set "ISCC_PATH=iscc"
    goto :compile
)

REM Check common installation locations
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    goto :compile
)

if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
    goto :compile
)

if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
    goto :compile
)

if exist "C:\Program Files\Inno Setup 5\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 5\ISCC.exe"
    goto :compile
)

echo [แจ้งเตือน] ไม่พบโปรแกรม Inno Setup Compiler (ISCC.exe) ในเครื่อง
echo.
echo คุณสามารถ:
echo 1. เปิดไฟล์ "installer_inno.iss" ด้วยโปรแกรม Inno Setup Compiler แล้วกด F9 (Compile)
echo 2. หรือดาวน์โหลด Inno Setup ได้ฟรีที่: https://jrsoftware.org/isdl.php
echo.
pause
exit /b 1

:compile
echo ตรวจพบ Inno Setup ที่: "%ISCC_PATH%"
echo กำลังคอมไพล์ installer_inno.iss...
echo.

"%ISCC_PATH%" "%~dp0installer_inno.iss"
if %errorlevel% neq 0 (
    echo.
    echo [ข้อผิดพลาด] การคอมไพล์ Inno Setup ล้มเหลว
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo    [สำเร็จ] สร้างตัวติดตั้ง CODS ด้วย Inno Setup เรียบร้อยแล้ว!
echo ======================================================================
echo ไฟล์ติดตั้ง: dist_installer\CODS_Setup_v1.0.exe
echo.
pause
exit /b 0
