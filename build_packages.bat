@echo off
title JADS - ตัวช่วยคอมไพล์และจัดทำแพ็กเกจ (Build Packages)
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================================
echo    JADS - Build & Packaging System
echo    สร้างแพ็กเกจทั้งแบบ Portable และ GUI Wizard Installer
echo ======================================================================
echo.

echo [1/6] ตรวจสอบไฟล์โลโก้และสร้าง logo.ico...
python -c "from PySide6.QtGui import QImage; img = QImage('logo.png'); img.save('logo.ico')"

echo [2/6] คอมไพล์โปรแกรมหลัก JADS ด้วย PyInstaller...
python -m PyInstaller jads.spec --noconfirm
if errorlevel 1 (
    echo [ข้อผิดพลาด] การคอมไพล์ PyInstaller ล้มเหลว
    pause
    exit /b 1
)

echo [3/6] คัดลอกแม่แบบ Word และไฟล์ที่เกี่ยวข้องไปยังชุดโปรแกรม...
if not exist "dist\JADS\templates" mkdir "dist\JADS\templates"
xcopy "templates\*" "dist\JADS\templates\" /E /I /Y /Q >nul
copy /y "logo.ico" "dist\JADS\" >nul
copy /y "logo.png" "dist\JADS\" >nul

echo [4/6] จัดเตรียมชุดพกพา (Portable Edition)...
copy /y "dist\JADS\JADS-Portable.bat" "dist\JADS\" 2>nul
copy /y "dist\JADS\README_PORTABLE.txt" "dist\JADS\" 2>nul

echo [5/6] บีบอัดไฟล์ ZIP สำหรับ Portable Edition...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'dist\JADS\*' -DestinationPath 'JADS_Portable_v1.0.zip' -Force"

echo [6/6] คอมไพล์ตัวติดตั้งอัตโนมัติ GUI Wizard (JADS_Setup_v1.0.exe)...
python -m PyInstaller --onefile --windowed --name JADS_Setup --icon logo.ico --add-data "JADS_Portable_v1.0.zip;." --add-data "logo.ico;." --add-data "logo.png;." installer_gui.py --noconfirm
copy /y "dist\JADS_Setup.exe" "JADS_Setup_v1.0.exe" >nul

echo.
echo ======================================================================
echo    [สำเร็จ] การสร้างแพ็กเกจเสร็จสมบูรณ์ 100%%
echo ======================================================================
echo - ตัวติดตั้ง GUI Wizard:   JADS_Setup_v1.0.exe (ดับเบิลคลิกเพื่อเปิดหน้าต่างติดตั้ง)
echo - ไฟล์บีบอัด Portable:      JADS_Portable_v1.0.zip (สำหรับนำไปแจกจ่าย/ใส่ Flash Drive)
echo - โฟลเดอร์ Portable พร้อมรัน: dist\JADS\ (ดับเบิลคลิก JADS.exe ใช้งานได้ทันที)
echo - สคริปต์ติดตั้งแบบ Batch:    install.bat (รันเพื่อติดตั้งอย่างรวดเร็ว)
echo.
pause
