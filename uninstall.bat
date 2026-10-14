@echo off
title CODS - ถอนการติดตั้งโปรแกรม
chcp 65001 >nul
echo ======================================================================
echo    คุณกำลังจะถอนการติดตั้ง CODS ออกจากคอมพิวเตอร์
echo ======================================================================
echo.

set "TARGET_DIR=%LOCALAPPDATA%\Programs\CODS"

if not exist "%TARGET_DIR%" (
    echo [แจ้งเตือน] ไม่พบการติดตั้ง CODS ในโฟลเดอร์ %TARGET_DIR%
    pause
    exit /b 0
)

set /p CONFIRM="ยืนยันการถอนการติดตั้ง CODS หรือไม่? (Y/N): "
if /i "%CONFIRM%" neq "Y" exit /b 0

echo.
echo กำลังลบ Shortcut บน Desktop และ Start Menu...
if exist "%USERPROFILE%\Desktop\CODS.lnk" del /f /q "%USERPROFILE%\Desktop\CODS.lnk"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\CODS" rd /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\CODS"

echo.
set /p DELDATA="ต้องการลบฐานข้อมูลและประวัติการตั้งค่าทั้งหมดด้วยหรือไม่? (Y/N): "
if /i "%DELDATA%"=="Y" (
    rd /s /q "%TARGET_DIR%\data" 2>nul
)

echo กำลังลบไฟล์โปรแกรม...
rd /s /q "%TARGET_DIR%" 2>nul

echo.
echo ======================================================================
echo    [สำเร็จ] ถอนการติดตั้ง CODS เรียบร้อยแล้ว
echo ======================================================================
pause
exit /b 0
