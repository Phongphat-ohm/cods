"""
CODS GUI Installation Wizard
Standalone Graphical Installer for Court Official Document System (CODS)
100% Offline & Air-Gapped Windows GUI Installer built with PySide6
"""

import sys
import os
import shutil
import zipfile
import subprocess
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QDialog, QStackedWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QProgressBar,
    QCheckBox, QFrame, QMessageBox, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QFont, QPainter
from PySide6.QtSvg import QSvgRenderer


def _make_check_pixmap(size: int = 15, color: str = "#16a34a") -> QPixmap:
    """Render a self-contained vector check icon (no emoji, no external assets)."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
        '<polyline points="20 6 9 17 4 12"/></svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    return pixmap


def get_resource_path(relative_path: str) -> str:
    """Resolve absolute path to resource, working for dev and PyInstaller onefile."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative_path)


class InstallWorker(QThread):
    """Background worker thread to perform file extraction and shortcut creation."""
    progress_updated = Signal(int, str)
    install_finished = Signal(bool, str)

    def __init__(self, target_dir: str, create_desktop: bool, create_startmenu: bool):
        super().__init__()
        self.target_dir = target_dir
        self.create_desktop = create_desktop
        self.create_startmenu = create_startmenu

    def run(self):
        try:
            os.makedirs(self.target_dir, exist_ok=True)

            # 1. Locate zip payload (CODS or JADS)
            zip_path = get_resource_path("CODS_Portable_v1.0.zip")
            if not os.path.exists(zip_path):
                zip_path = get_resource_path("JADS_Portable_v1.0.zip")
            if not os.path.exists(zip_path):
                # Fallback to local directory
                cwd_zip = os.path.join(os.getcwd(), "CODS_Portable_v1.0.zip")
                if not os.path.exists(cwd_zip):
                    cwd_zip = os.path.join(os.getcwd(), "JADS_Portable_v1.0.zip")
                if os.path.exists(cwd_zip):
                    zip_path = cwd_zip

            if os.path.exists(zip_path):
                self.progress_updated.emit(5, "กำลังเปิดชุดไฟล์ติดตั้ง...")
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    members = zf.infolist()
                    total = len(members)
                    for idx, member in enumerate(members):
                        zf.extract(member, self.target_dir)
                        pct = int(5 + (idx / total) * 75)
                        short_name = os.path.basename(member.filename) or member.filename
                        self.progress_updated.emit(pct, f"กำลังคัดลอก: {short_name}")
            else:
                # If zip not found, look for dist/CODS or dist/JADS
                dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "CODS")
                if not os.path.exists(dist_dir):
                    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "JADS")
                if os.path.exists(dist_dir):
                    self.progress_updated.emit(20, "กำลังคัดลอกไฟล์จาก dist...")
                    for root, dirs, files in os.walk(dist_dir):
                        rel_root = os.path.relpath(root, dist_dir)
                        dest_root = os.path.join(self.target_dir, rel_root) if rel_root != "." else self.target_dir
                        os.makedirs(dest_root, exist_ok=True)
                        for f in files:
                            src_f = os.path.join(root, f)
                            dst_f = os.path.join(dest_root, f)
                            shutil.copy2(src_f, dst_f)
                else:
                    self.install_finished.emit(False, "ไม่พบไฟล์แพ็กเกจสำหรับการติดตั้ง (CODS_Portable_v1.0.zip)")
                    return

            self.progress_updated.emit(85, "กำลังสร้างตัวถอนการติดตั้ง (Uninstaller)...")
            self.create_uninstaller()

            self.progress_updated.emit(90, "กำลังสร้างทางลัด (Shortcuts)...")
            self.create_shortcuts()

            self.progress_updated.emit(100, "การติดตั้งเสร็จสมบูรณ์!")
            self.install_finished.emit(True, "สำเร็จ")

        except Exception as e:
            self.install_finished.emit(False, str(e))

    def create_uninstaller(self):
        """Create clean uninstall.bat script in target directory."""
        uninstaller_content = f"""@echo off
title CODS - ถอนการติดตั้งโปรแกรม
chcp 65001 >nul
echo ======================================================================
echo    คุณกำลังจะถอนการติดตั้ง CODS ออกจากคอมพิวเตอร์
echo ======================================================================
echo.
set /p CONFIRM="ยืนยันการถอนการติดตั้งหรือไม่? (Y/N): "
if /i "%CONFIRM%" neq "Y" exit /b 0

echo กำลังลบ Shortcut บน Desktop และ Start Menu...
if exist "%USERPROFILE%\\Desktop\\CODS.lnk" del /f /q "%USERPROFILE%\\Desktop\\CODS.lnk"
if exist "%USERPROFILE%\\Desktop\\JADS.lnk" del /f /q "%USERPROFILE%\\Desktop\\JADS.lnk"
if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\CODS" rd /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\CODS"
if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\JADS" rd /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\JADS"

echo.
set /p DELDATA="ต้องการลบฐานข้อมูลและประวัติการตั้งค่าทั้งหมดด้วยหรือไม่? (Y/N): "
if /i "%DELDATA%"=="Y" (
    rd /s /q "{self.target_dir}\\data" 2>nul
)

echo กำลังลบไฟล์โปรแกรม...
start "" cmd /c "timeout /t 1 /nobreak >nul & rd /s /q \"{self.target_dir}\""
echo ถอนการติดตั้ง CODS เรียบร้อยแล้ว
pause
"""
        uninstaller_path = os.path.join(self.target_dir, "uninstall.bat")
        with open(uninstaller_path, "w", encoding="utf-8") as f:
            f.write(uninstaller_content)

    def create_shortcuts(self):
        """Create Windows desktop and start menu shortcuts via PowerShell."""
        exe_path = os.path.join(self.target_dir, "CODS.exe")
        if not os.path.exists(exe_path):
            alt_exe = os.path.join(self.target_dir, "JADS.exe")
            if os.path.exists(alt_exe):
                exe_path = alt_exe

        icon_path = os.path.join(self.target_dir, "logo.ico")
        un_path = os.path.join(self.target_dir, "uninstall.bat")

        ps_script = []
        ps_script.append("$wsh = New-Object -ComObject WScript.Shell;")

        if self.create_desktop:
            ps_script.append(f"""
            $desktop = [Environment]::GetFolderPath('Desktop');
            $scDesktop = $wsh.CreateShortcut((Join-Path $desktop 'CODS.lnk'));
            $scDesktop.TargetPath = '{exe_path}';
            $scDesktop.WorkingDirectory = '{self.target_dir}';
            $scDesktop.IconLocation = '{icon_path},0';
            $scDesktop.Description = 'ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม (CODS)';
            $scDesktop.Save();
            """)

        if self.create_startmenu:
            ps_script.append(f"""
            $startPrograms = [Environment]::GetFolderPath('Programs');
            $menuFolder = Join-Path $startPrograms 'CODS';
            if (!(Test-Path $menuFolder)) {{ New-Item -ItemType Directory -Path $menuFolder -Force | Out-Null }};
            $scStart = $wsh.CreateShortcut((Join-Path $menuFolder 'CODS.lnk'));
            $scStart.TargetPath = '{exe_path}';
            $scStart.WorkingDirectory = '{self.target_dir}';
            $scStart.IconLocation = '{icon_path},0';
            $scStart.Description = 'ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม (CODS)';
            $scStart.Save();
            $scUn = $wsh.CreateShortcut((Join-Path $menuFolder 'Uninstall CODS.lnk'));
            $scUn.TargetPath = '{un_path}';
            $scUn.WorkingDirectory = '{self.target_dir}';
            $scUn.Description = 'ถอนการติดตั้ง CODS';
            $scUn.Save();
            """)

        full_cmd = " ".join(ps_script)
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", full_cmd],
            capture_output=True,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )


class InstallerWizardDialog(QDialog):
    """Main Graphical Setup Wizard Dialog."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ติดตั้ง CODS - Court Official Document System (v1.0)")
        self.resize(680, 470)
        self.setMinimumSize(640, 440)

        # Set Window Icon
        logo_path = get_resource_path("logo.ico")
        if not os.path.exists(logo_path):
            logo_path = get_resource_path("logo.png")
        if os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        default_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        self.default_install_dir = os.path.join(default_appdata, "Programs", "CODS")

        self.worker: Optional[InstallWorker] = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
                font-family: 'Kanit', 'Segoe UI', Tahoma, sans-serif;
            }
            QLabel {
                color: #1e293b;
            }
            QPushButton {
                font-size: 13.5px;
                font-weight: 500;
                padding: 7px 18px;
                border-radius: 6px;
            }
            QPushButton#btnPrimary {
                background-color: #4c1d95;
                color: #ffffff;
                font-weight: 600;
                border: none;
            }
            QPushButton#btnPrimary:hover {
                background-color: #5b21b6;
            }
            QPushButton#btnPrimary:pressed {
                background-color: #3b0764;
            }
            QPushButton#btnPrimary:disabled {
                background-color: #94a3b8;
                color: #e2e8f0;
            }
            QPushButton#btnSecondary {
                background-color: #ffffff;
                color: #334155;
                border: 1.5px solid #cbd5e1;
            }
            QPushButton#btnSecondary:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 7px 12px;
                font-size: 13px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border-color: #7c3aed;
            }
            QCheckBox {
                font-size: 13px;
                color: #334155;
                spacing: 8px;
            }
            QProgressBar {
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                text-align: center;
                background-color: #ffffff;
                height: 22px;
                font-size: 12px;
                font-weight: 600;
                color: #1e293b;
            }
            QProgressBar::chunk {
                background-color: #6d28d9;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stacked Pages
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.init_welcome_page()
        self.init_directory_page()
        self.init_progress_page()
        self.init_finished_page()

        # Bottom Action Bar
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("background-color: #f1f5f9; border-top: 1px solid #e2e8f0;")
        h_bottom = QHBoxLayout(bottom_bar)
        h_bottom.setContentsMargins(20, 12, 20, 12)
        h_bottom.setSpacing(10)

        self.btn_cancel = QPushButton("ยกเลิก")
        self.btn_cancel.setObjectName("btnSecondary")
        self.btn_cancel.clicked.connect(self.close)
        h_bottom.addWidget(self.btn_cancel)

        h_bottom.addStretch()

        self.btn_back = QPushButton("< ย้อนกลับ")
        self.btn_back.setObjectName("btnSecondary")
        self.btn_back.setVisible(False)
        self.btn_back.clicked.connect(self.go_back)
        h_bottom.addWidget(self.btn_back)

        self.btn_next = QPushButton("ถัดไป >")
        self.btn_next.setObjectName("btnPrimary")
        self.btn_next.clicked.connect(self.go_next)
        h_bottom.addWidget(self.btn_next)

        layout.addWidget(bottom_bar)

    # -------------------------------------------------------------------------
    # Page 0: Welcome Page
    # -------------------------------------------------------------------------
    def init_welcome_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(32, 28, 32, 24)
        lay.setSpacing(16)

        # Header with Logo
        h_top = QHBoxLayout()
        h_top.setSpacing(16)

        logo_lbl = QLabel()
        logo_path = get_resource_path("logo.png")
        if os.path.exists(logo_path):
            pm = QPixmap(logo_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(pm)
        h_top.addWidget(logo_lbl)

        v_title = QVBoxLayout()
        lbl_app = QLabel("ยินดีต้อนรับสู่การติดตั้ง CODS")
        lbl_app.setStyleSheet("font-size: 20px; font-weight: 700; color: #4c1d95;")
        lbl_sub = QLabel("Court Official Document System (v1.0.0)")
        lbl_sub.setStyleSheet("font-size: 13.5px; color: #64748b; font-weight: 500;")
        v_title.addWidget(lbl_app)
        v_title.addWidget(lbl_sub)
        h_top.addLayout(v_title)
        h_top.addStretch()
        lay.addLayout(h_top)

        # Description Card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        v_card = QVBoxLayout(card)
        v_card.setSpacing(10)

        lbl_desc = QLabel("โปรแกรมจะทำการติดตั้งระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอมลงในเครื่องคอมพิวเตอร์ของคุณ:")
        lbl_desc.setStyleSheet("font-size: 13.5px; line-height: 1.4;")
        lbl_desc.setWordWrap(True)
        v_card.addWidget(lbl_desc)

        features = [
            "<b>100% Offline & Air-Gapped:</b> ทำงานแบบปิดสมบูรณ์ ปลอดภัยต่อข้อมูลคดี ไม่ต้องใช้อินเทอร์เน็ต",
            "<b>ฐานข้อมูล SQLite ในตัว:</b> จัดเก็บข้อมูลคู่องค์คณะและแม่แบบย่อหน้าอย่างถาวรและแม่นยำ",
            "<b>สิทธิ์ผู้ใช้มาตรฐาน (Non-Admin):</b> ไม่จำเป็นต้องใช้สิทธิ์ Administrator ในการติดตั้ง",
            "<b>สะดวก รวดเร็ว:</b> สร้างไอคอนทางลัดบนหน้าจอ Desktop และ Start Menu อัตโนมัติ"
        ]
        check_pm = _make_check_pixmap(15)
        for f in features:
            row = QHBoxLayout()
            row.setSpacing(8)
            ico = QLabel()
            ico.setPixmap(check_pm)
            ico.setFixedSize(16, 16)
            row.addWidget(ico, 0, Qt.AlignmentFlag.AlignTop)
            l = QLabel(f)
            l.setStyleSheet("font-size: 13px; color: #334155;")
            l.setWordWrap(True)
            row.addWidget(l, 1)
            v_card.addLayout(row)

        lay.addWidget(card)
        lay.addStretch()

        self.stack.addWidget(page)

    # -------------------------------------------------------------------------
    # Page 1: Directory Selection & Options
    # -------------------------------------------------------------------------
    def init_directory_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(32, 24, 32, 20)
        lay.setSpacing(14)

        lbl_head = QLabel("เลือกโฟลเดอร์สำหรับติดตั้ง")
        lbl_head.setStyleSheet("font-size: 17px; font-weight: 700; color: #4c1d95;")
        lay.addWidget(lbl_head)

        lbl_sub = QLabel("ระบบจะติดตั้งไฟล์โปรแกรมและฐานข้อมูลลงในโฟลเดอร์ต่อไปนี้ (สามารถเปลี่ยนได้ตามต้องการ):")
        lbl_sub.setStyleSheet("font-size: 13px; color: #475569;")
        lay.addWidget(lbl_sub)

        # Path input
        h_dir = QHBoxLayout()
        self.txt_path = QLineEdit(self.default_install_dir)
        h_dir.addWidget(self.txt_path, 1)

        btn_browse = QPushButton("เรียกดู...")
        btn_browse.setObjectName("btnSecondary")
        btn_browse.clicked.connect(self.browse_install_dir)
        h_dir.addWidget(btn_browse)
        lay.addLayout(h_dir)

        # Space label
        self.lbl_space = QLabel(self.get_disk_space_text())
        self.lbl_space.setStyleSheet("font-size: 12.5px; color: #64748b;")
        lay.addWidget(self.lbl_space)

        # Additional tasks group
        lay.addSpacing(6)
        lbl_tasks = QLabel("ตัวเลือกเพิ่มเติม:")
        lbl_tasks.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")
        lay.addWidget(lbl_tasks)

        self.chk_desktop = QCheckBox("สร้างไอคอนทางลัดบนหน้าจอเดสก์ท็อป (Desktop Shortcut)")
        self.chk_desktop.setChecked(True)
        lay.addWidget(self.chk_desktop)

        self.chk_startmenu = QCheckBox("สร้างทางลัดในเมนูเริ่มต้น (Start Menu -> CODS)")
        self.chk_startmenu.setChecked(True)
        lay.addWidget(self.chk_startmenu)

        lay.addStretch()
        self.stack.addWidget(page)

    # -------------------------------------------------------------------------
    # Page 2: Progress Page
    # -------------------------------------------------------------------------
    def init_progress_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(32, 36, 32, 36)
        lay.setSpacing(16)

        lbl_head = QLabel("กำลังติดตั้งโปรแกรม CODS...")
        lbl_head.setStyleSheet("font-size: 18px; font-weight: 700; color: #4c1d95;")
        lay.addWidget(lbl_head)

        self.lbl_prog_status = QLabel("กรุณารอสักครู่ ระบบกำลังคัดลอกไฟล์และตั้งค่าโปรแกรม...")
        self.lbl_prog_status.setStyleSheet("font-size: 13px; color: #475569;")
        lay.addWidget(self.lbl_prog_status)

        lay.addSpacing(10)
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        lay.addWidget(self.pbar)

        self.lbl_file_status = QLabel("")
        self.lbl_file_status.setStyleSheet("font-size: 12px; color: #64748b;")
        lay.addWidget(self.lbl_file_status)

        lay.addStretch()
        self.stack.addWidget(page)

    # -------------------------------------------------------------------------
    # Page 3: Finished Page
    # -------------------------------------------------------------------------
    def init_finished_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(32, 32, 32, 28)
        lay.setSpacing(16)

        lbl_head = QLabel("การติดตั้งเสร็จสมบูรณ์!")
        lbl_head.setStyleSheet("font-size: 20px; font-weight: 700; color: #15803d;")
        lay.addWidget(lbl_head)

        lbl_sub = QLabel("ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม (CODS) พร้อมใช้งานแล้ว")
        lbl_sub.setStyleSheet("font-size: 14px; color: #334155; font-weight: 500;")
        lay.addWidget(lbl_sub)

        # Summary box
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1.5px solid #dcfce7;
                border-radius: 8px;
                padding: 14px;
            }
        """)
        v_card = QVBoxLayout(card)
        v_card.setSpacing(8)

        self.lbl_final_dir = QLabel()
        self.lbl_final_dir.setStyleSheet("font-size: 13px; color: #1e293b;")
        v_card.addWidget(self.lbl_final_dir)

        lbl_info = QLabel("• ฐานข้อมูลและการตั้งค่าทั้งหมดถูกติดตั้งพร้อมทำงานแบบ 100% Offline\n• มีไอคอนทางลัดสำหรับเปิดใช้งานทันที")
        lbl_info.setStyleSheet("font-size: 12.5px; color: #475569; line-height: 1.4;")
        v_card.addWidget(lbl_info)
        lay.addWidget(card)

        self.chk_launch = QCheckBox("เปิดใช้งานโปรแกรม CODS ทันที")
        self.chk_launch.setChecked(True)
        self.chk_launch.setStyleSheet("font-size: 14px; font-weight: 600; color: #4c1d95;")
        lay.addWidget(self.chk_launch)

        lay.addStretch()
        self.stack.addWidget(page)

    # -------------------------------------------------------------------------
    # Navigation & Actions
    # -------------------------------------------------------------------------
    def browse_install_dir(self):
        dir_selected = QFileDialog.getExistingDirectory(self, "เลือกโฟลเดอร์ติดตั้ง", self.txt_path.text())
        if dir_selected:
            final_dir = os.path.join(dir_selected, "CODS") if not (dir_selected.endswith("CODS") or dir_selected.endswith("JADS")) else dir_selected
            self.txt_path.setText(final_dir)
            self.lbl_space.setText(self.get_disk_space_text(final_dir))

    def get_disk_space_text(self, path: str = "") -> str:
        try:
            target = path or self.txt_path.text() or self.default_install_dir
            drive = os.path.splitdrive(os.path.abspath(target))[0] or "C:"
            total, used, free = shutil.disk_usage(drive)
            free_gb = free / (1024 ** 3)
            return f"พื้นที่ว่างบนไดรฟ์ {drive}: {free_gb:.1f} GB (ต้องการพื้นที่ประมาณ 180 MB)"
        except Exception:
            return "ต้องการพื้นที่ว่างประมาณ 180 MB"

    def go_next(self):
        curr = self.stack.currentIndex()
        if curr == 0:
            self.stack.setCurrentIndex(1)
            self.btn_back.setVisible(True)
            self.btn_next.setText("ติดตั้ง >")
        elif curr == 1:
            target_dir = self.txt_path.text().strip()
            if not target_dir:
                QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุโฟลเดอร์สำหรับติดตั้ง")
                return
            self.start_installation(target_dir)
        elif curr == 3:
            # Finished Page -> Done
            if self.chk_launch.isChecked():
                target_base = self.txt_path.text().strip()
                exe_path = os.path.join(target_base, "CODS.exe")
                if not os.path.exists(exe_path):
                    alt_exe = os.path.join(target_base, "JADS.exe")
                    if os.path.exists(alt_exe):
                        exe_path = alt_exe
                if os.path.exists(exe_path):
                    subprocess.Popen([exe_path], cwd=target_base)
            self.accept()

    def go_back(self):
        curr = self.stack.currentIndex()
        if curr == 1:
            self.stack.setCurrentIndex(0)
            self.btn_back.setVisible(False)
            self.btn_next.setText("ถัดไป >")

    def start_installation(self, target_dir: str):
        self.stack.setCurrentIndex(2)
        self.btn_back.setVisible(False)
        self.btn_next.setEnabled(False)
        self.btn_cancel.setEnabled(False)

        self.worker = InstallWorker(
            target_dir=target_dir,
            create_desktop=self.chk_desktop.isChecked(),
            create_startmenu=self.chk_startmenu.isChecked()
        )
        self.worker.progress_updated.connect(self.on_progress)
        self.worker.install_finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, pct: int, msg: str):
        self.pbar.setValue(pct)
        self.lbl_file_status.setText(msg)

    def on_finished(self, success: bool, err_msg: str):
        if success:
            self.lbl_final_dir.setText(f"<b>โฟลเดอร์ติดตั้ง:</b> {self.txt_path.text().strip()}")
            self.stack.setCurrentIndex(3)
            self.btn_next.setText("เสร็จสิ้น")
            self.btn_next.setEnabled(True)
            self.btn_cancel.setVisible(False)
        else:
            QMessageBox.critical(self, "ข้อผิดพลาดในการติดตั้ง", f"เกิดข้อผิดพลาดระหว่างการติดตั้ง:\n\n{err_msg}")
            self.stack.setCurrentIndex(1)
            self.btn_back.setVisible(True)
            self.btn_next.setEnabled(True)
            self.btn_cancel.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    wizard = InstallerWizardDialog()
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
