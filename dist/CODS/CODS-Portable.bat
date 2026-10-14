@echo off
title CODS - Court Official Document System (Portable)
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================================
echo    CODS - Court Official Document System (ระบบจัดการเอกสารศาล)
echo    100%% Offline & Air-Gapped - Portable Edition
echo ======================================================================
echo.
echo กำลังเปิดโปรแกรม CODS...
echo ข้อมูลทั้งหมดจะถูกบันทึกไว้ในโฟลเดอร์ data/jads.db ภายในไดรฟ์นี้
echo.

start "" "%~dp0CODS.exe"
exit /b 0
