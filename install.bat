@echo off
setlocal enabledelayedexpansion
title CODS - ระบบติดตั้งโปรแกรม (Windows Installer)
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================================
echo    CODS - Court Official Document System (ระบบจัดการเอกสารศาล)
echo    100%% Offline & Air-Gapped - Windows Installer
echo ======================================================================
echo.

set "SOURCE_DIR=%~dp0dist\CODS"
if not exist "%SOURCE_DIR%\CODS.exe" (
    set "SOURCE_DIR=%~dp0dist\JADS"
)

if not exist "%SOURCE_DIR%" (
    echo [ข้อผิดพลาด] ไม่พบไฟล์โปรแกรมที่คอมไพล์แล้วในโฟลเดอร์ dist\CODS
    echo กำลังดำเนินการคอมไพล์อัตโนมัติ...
    call "%~dp0build_packages.bat"
)

set "TARGET_DIR=%LOCALAPPDATA%\Programs\CODS"
echo [1/4] กำลังจัดเตรียมโฟลเดอร์ติดตั้ง: "%TARGET_DIR%"
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo [2/4] กำลังคัดลอกไฟล์โปรแกรมและส่วนประกอบทั้งหมด...
xcopy "%SOURCE_DIR%\*" "%TARGET_DIR%\" /E /I /Y /Q >nul
if exist "%TARGET_DIR%\JADS.exe" (
    if not exist "%TARGET_DIR%\CODS.exe" copy /y "%TARGET_DIR%\JADS.exe" "%TARGET_DIR%\CODS.exe" >nul
)

echo [3/4] กำลังสร้างตัวถอนการติดตั้ง (Uninstaller)...
(
    echo @echo off
    echo title CODS - ถอนการติดตั้งโปรแกรม
    echo chcp 65001 ^>nul
    echo echo ======================================================================
    echo echo    คุณกำลังจะถอนการติดตั้ง CODS ออกจากคอมพิวเตอร์
    echo echo ======================================================================
    echo echo.
    echo set /p CONFIRM="ยืนยันการถอนการติดตั้งหรือไม่? (Y/N): "
    echo if /i "%%CONFIRM%%" neq "Y" exit /b 0
    echo.
    echo กำลังลบ Shortcut บน Desktop และ Start Menu...
    echo if exist "%%USERPROFILE%%\Desktop\CODS.lnk" del /f /q "%%USERPROFILE%%\Desktop\CODS.lnk"
    echo if exist "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\CODS" rd /s /q "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\CODS"
    echo.
    echo set /p DELDATA="ต้องการลบฐานข้อมูลและประวัติการตั้งค่าทั้งหมดด้วยหรือไม่? (Y/N): "
    echo if /i "%%DELDATA%%"=="Y" (
    echo     rd /s /q "%TARGET_DIR%\data" 2^>nul
    echo )
    echo.
    echo กำลังลบไฟล์โปรแกรม...
    echo start "" cmd /c "timeout /t 1 /nobreak >nul & rd /s /q \"%TARGET_DIR%\""
    echo echo ถอนการติดตั้ง CODS เรียบร้อยแล้ว
    echo pause
) > "%TARGET_DIR%\uninstall.bat"

echo [4/4] กำลังสร้างทางลัดบน Desktop และ Start Menu...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_shortcuts.ps1" -TargetDir "%TARGET_DIR%"

echo.
echo ======================================================================
echo    [สำเร็จ] ติดตั้งโปรแกรม CODS เรียบร้อยแล้ว!
echo ======================================================================
echo - โฟลเดอร์ติดตั้ง: %TARGET_DIR%
echo - ทางลัดหน้าจอ:    Desktop -> CODS.lnk
echo - เมนูเริ่มต้น:    Start Menu -> CODS -> CODS.lnk
echo.
set /p LAUNCH="ต้องการเปิดโปรแกรมทันทีหรือไม่? (Y/N) [ค่าเริ่มต้น: Y]: "
if /i "%LAUNCH%"=="" set "LAUNCH=Y"
if /i "%LAUNCH%"=="Y" (
    if exist "%TARGET_DIR%\CODS.exe" (
        start "" "%TARGET_DIR%\CODS.exe"
    ) else (
        start "" "%TARGET_DIR%\JADS.exe"
    )
)
exit /b 0
