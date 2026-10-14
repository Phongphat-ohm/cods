@echo off
title JADS - Judicial Automated Document System (Portable)
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================================
echo    JADS - Judicial Automated Document System (ระบบจัดการเอกสารศาล)
echo    100%% Offline & Air-Gapped - Portable Edition
echo ======================================================================
echo.
echo กำลังเปิดโปรแกรม JADS...
echo ข้อมูลทั้งหมดจะถูกบันทึกไว้ในโฟลเดอร์ data/jads.db ภายในไดรฟ์นี้
echo.

start "" "%~dp0JADS.exe"
exit /b 0
