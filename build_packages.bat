@echo off
title CODS - ตัวช่วยคอมไพล์และจัดทำแพ็กเกจ (Build Packages)
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================================
echo    CODS - Build & Packaging System
echo    สร้างแพ็กเกจทั้งแบบ Portable และ GUI Wizard Installer
echo ======================================================================
echo.

echo [1/6] ตรวจสอบไฟล์โลโก้และสร้าง logo.ico...
python -c "from PySide6.QtGui import QImage; img = QImage('logo.png'); img.save('logo.ico')"

echo [2/6] คอมไพล์โปรแกรมหลัก CODS ด้วย PyInstaller...
python -m PyInstaller cods.spec --noconfirm
if errorlevel 1 (
    echo [ข้อผิดพลาด] การคอมไพล์ PyInstaller ล้มเหลว
    pause
    exit /b 1
)

echo [3/6] คัดลอกแม่แบบ Word และไฟล์ที่เกี่ยวข้องไปยังชุดโปรแกรม...
if not exist "dist\CODS\templates" mkdir "dist\CODS\templates"
xcopy "templates\*" "dist\CODS\templates\" /E /I /Y /Q >nul
copy /y "logo.ico" "dist\CODS\" >nul
copy /y "logo.png" "dist\CODS\" >nul

echo [4/6] จัดเตรียมชุดพกพา (Portable Edition)...
copy /y "dist\CODS\CODS-Portable.bat" "dist\CODS\" 2>nul
copy /y "dist\CODS\README_PORTABLE.txt" "dist\CODS\" 2>nul

echo [5/6] บีบอัดไฟล์ ZIP สำหรับ Portable Edition...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'dist\CODS\*' -DestinationPath 'CODS_Portable_v1.0.zip' -Force"

echo [6/6] คอมไพล์ตัวติดตั้งอัตโนมัติ GUI Wizard (CODS_Setup_v1.0.exe)...
python -m PyInstaller --onefile --windowed --name CODS_Setup --icon logo.ico --add-data "CODS_Portable_v1.0.zip;." --add-data "logo.ico;." --add-data "logo.png;." installer_gui.py --noconfirm
copy /y "dist\CODS_Setup.exe" "CODS_Setup_v1.0.exe" >nul

echo.
echo ======================================================================
echo    [สำเร็จ] การสร้างแพ็กเกจเสร็จสมบูรณ์ 100%%
echo ======================================================================
echo - ตัวติดตั้ง GUI Wizard:   CODS_Setup_v1.0.exe (ดับเบิลคลิกเพื่อเปิดหน้าต่างติดตั้ง)
echo - ไฟล์บีบอัด Portable:      CODS_Portable_v1.0.zip (สำหรับนำไปแจกจ่าย/ใส่ Flash Drive)
echo - โฟลเดอร์ Portable พร้อมรัน: dist\CODS\ (ดับเบิลคลิก CODS.exe ใช้งานได้ทันที)
echo - สคริปต์ติดตั้งแบบ Batch:    install.bat (รันเพื่อติดตั้งอย่างรวดเร็ว)
echo.
pause
