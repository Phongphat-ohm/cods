"""
About Dialog Component for CODS (Court Official Document System)
Official Judicial Theme, System Specifications, Changelog, and Folder Access.
100% Offline & Air-Gapped.
"""

import sys
import os
import platform
import subprocess
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTabWidget, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap

import constants
import storage_service
from icon_service import get_icon, get_pixmap, get_app_logo_pixmap, get_app_logo_icon


def _open_folder_in_explorer(path: str):
    """Open a directory in Windows File Explorer safely."""
    try:
        if os.path.exists(path):
            if sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.Popen(["explorer", path])
    except Exception:
        pass


class AboutDialog(QDialog):
    """Comprehensive 'About CODS' modal dialog with system specs, changelog, and folder tools."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"เกี่ยวกับโปรแกรม - {constants.APP_NAME} (v{constants.APP_VERSION})")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(680, 560)
        self.setMinimumSize(620, 500)
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()
        QTimer.singleShot(0, self.center_on_parent)

    def center_on_parent(self):
        """Center the dialog perfectly on its parent window or active screen."""
        parent = self.parent()
        if parent and parent.isVisible():
            top_window = parent.window()
            base_rect = top_window.geometry()
        else:
            from PySide6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()
            base_rect = screen.availableGeometry() if screen else self.geometry()

        frame = self.frameGeometry()
        frame.moveCenter(base_rect.center())
        self.move(frame.topLeft())

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
                font-family: 'Kanit', 'Segoe UI', Tahoma, sans-serif;
            }
            QLabel {
                color: #1e293b;
            }
            QTabWidget::pane {
                border: 1.5px solid #e2e8f0;
                border-radius: 8px;
                background-color: #ffffff;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #f1f5f9;
                color: #64748b;
                font-weight: 500;
                font-size: 13px;
                padding: 8px 18px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                border: 1px solid #e2e8f0;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #4c1d95;
                font-weight: 600;
                border-color: #e2e8f0;
                border-bottom: 2px solid #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e2e8f0;
                color: #1e293b;
            }
            QPushButton#btnActionSmall {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                color: #4c1d95;
                font-weight: 500;
                font-size: 12.5px;
                padding: 5px 12px;
            }
            QPushButton#btnActionSmall:hover {
                background-color: #f5f3ff;
                border-color: #a78bfa;
                color: #4c1d95;
            }
            QPushButton#btnClose {
                background-color: #4c1d95;
                color: #ffffff;
                font-weight: 600;
                font-size: 13.5px;
                padding: 7px 24px;
                border-radius: 6px;
                border: none;
            }
            QPushButton#btnClose:hover {
                background-color: #5b21b6;
            }
            QPushButton#btnClose:pressed {
                background-color: #3b0764;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 18)
        layout.setSpacing(14)

        # ---------------------------------------------------------------------
        # Top Header (Hero Card)
        # ---------------------------------------------------------------------
        card_hero = QFrame()
        card_hero.setObjectName("aboutHeroCard")
        card_hero.setStyleSheet("""
            QFrame#aboutHeroCard {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 10px;
            }
        """)
        h_hero = QHBoxLayout(card_hero)
        h_hero.setSpacing(16)
        h_hero.setContentsMargins(18, 14, 18, 14)

        logo_lbl = QLabel()
        logo_lbl.setObjectName("aboutLogoLabel")
        logo_pixmap = get_app_logo_pixmap(size=64)
        logo_lbl.setPixmap(logo_pixmap)
        logo_lbl.setFixedSize(64, 64)
        logo_lbl.setScaledContents(False)
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet("QLabel#aboutLogoLabel { background: transparent; padding: 0px; border: none; }")
        h_hero.addWidget(logo_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        v_hero_info = QVBoxLayout()
        v_hero_info.setSpacing(4)

        lbl_app_name = QLabel(f"{constants.APP_NAME} - {constants.APP_FULL_NAME}")
        lbl_app_name.setStyleSheet("font-size: 17px; font-weight: 700; color: #4c1d95;")
        v_hero_info.addWidget(lbl_app_name)

        lbl_app_sub = QLabel(constants.APP_SUBTITLE)
        lbl_app_sub.setStyleSheet("font-size: 13px; color: #475569;")
        v_hero_info.addWidget(lbl_app_sub)

        # Badges row (Version, Date, Offline)
        h_badges = QHBoxLayout()
        h_badges.setSpacing(8)

        lbl_ver_badge = QLabel(f"เวอร์ชัน {constants.APP_VERSION}")
        lbl_ver_badge.setStyleSheet("""
            background-color: #f5f3ff;
            color: #5b21b6;
            border: 1px solid #ddd6fe;
            border-radius: 10px;
            font-size: 11.5px;
            font-weight: 600;
            padding: 2px 9px;
        """)
        h_badges.addWidget(lbl_ver_badge)

        lbl_date_badge = QLabel(constants.APP_RELEASE_DATE)
        lbl_date_badge.setStyleSheet("""
            background-color: #f1f5f9;
            color: #475569;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            font-size: 11.5px;
            padding: 2px 9px;
        """)
        h_badges.addWidget(lbl_date_badge)

        lbl_offline_badge = QLabel("100% Offline (Air-Gapped)")
        lbl_offline_badge.setStyleSheet("""
            background-color: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
            border-radius: 10px;
            font-size: 11.5px;
            font-weight: 600;
            padding: 2px 9px;
        """)
        h_badges.addWidget(lbl_offline_badge)
        h_badges.addStretch()

        v_hero_info.addLayout(h_badges)
        h_hero.addLayout(v_hero_info, 1)

        layout.addWidget(card_hero)

        # ---------------------------------------------------------------------
        # Tab Widget
        # ---------------------------------------------------------------------
        tabs = QTabWidget()
        tabs.addTab(self.create_overview_tab(), "ภาพรวมระบบ")
        tabs.addTab(self.create_changelog_tab(), "ประวัติการอัปเดต (Changelog)")
        tabs.addTab(self.create_specs_tab(), "ข้อมูลสเปก & สภาพแวดล้อม")
        layout.addWidget(tabs, 1)

        # ---------------------------------------------------------------------
        # Bottom Button Bar
        # ---------------------------------------------------------------------
        h_bottom = QHBoxLayout()
        h_bottom.setSpacing(10)

        lbl_org = QLabel(f"หน่วยงาน: {constants.APP_ORGANIZATION}")
        lbl_org.setStyleSheet("font-size: 12px; color: #64748b;")
        h_bottom.addWidget(lbl_org)

        h_bottom.addStretch()

        btn_close = QPushButton("ปิด")
        btn_close.setObjectName("btnClose")
        btn_close.clicked.connect(self.accept)
        h_bottom.addWidget(btn_close)

        layout.addLayout(h_bottom)

    # -------------------------------------------------------------------------
    # Tab 1: Overview Tab
    # -------------------------------------------------------------------------
    def create_overview_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(14)

        lbl_desc = QLabel(
            "<b>CODS (Court Official Document System)</b> เป็นระบบคอมพิวเตอร์ช่วยเจ้าหน้าที่ธุรการศาลและศาลยุติธรรม "
            "จัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม จากไฟล์ตารางนัด Excel (.xlsx) สู่เอกสารราชการ Microsoft Word (.docx) "
            "ตามแบบพิมพ์มาตรฐาน ๒๒ ของสำนักงานศาลยุติธรรมอย่างแม่นยำและรวดเร็ว"
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 13px; line-height: 1.5; color: #334155;")
        lay.addWidget(lbl_desc)

        # Key Highlights Box
        box_hl = QFrame()
        box_hl.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        v_hl = QVBoxLayout(box_hl)
        v_hl.setSpacing(6)

        highlights = [
            ("100% Offline & Air-Gapped", "ทำงานภายในเครื่อง 100% ไม่ส่งข้อมูลออกภายนอก ปลอดภัยตามมาตรฐานศาล"),
            ("ระบบฐานข้อมูล SQLite ในตัว", "จัดเก็บข้อมูลคู่บัลลังก์ แม่แบบย่อหน้า และการตั้งค่าอย่างถาวรด้วย ACID & WAL"),
            ("จับคู่บัลลังก์ & จัดลำดับผู้มาศาล", "จดจำคู่ผู้พิพากษาอัตโนมัติ และจัดเรียงลำดับผู้มาศาลตามธรรมเนียมปฏิบัติ"),
            ("ระบบบำรุงรักษา Inno Setup", "รองรับการอัปเดตเวอร์ชัน ซ่อมแซมระบบ และปกป้องข้อมูลคดีเดิม 100%")
        ]
        for title, desc in highlights:
            row = QHBoxLayout()
            row.setSpacing(8)
            ico = QLabel()
            ico.setPixmap(get_pixmap("check", color="#16a34a", size=14))
            row.addWidget(ico, 0, Qt.AlignmentFlag.AlignTop)
            lbl = QLabel(f"<b>{title}:</b> {desc}")
            lbl.setStyleSheet("font-size: 12.5px; color: #334155;")
            lbl.setWordWrap(True)
            row.addWidget(lbl, 1)
            v_hl.addLayout(row)

        lay.addWidget(box_hl)

        # Folder paths & Action buttons
        lay.addSpacing(2)
        lbl_folders_title = QLabel("ตำแหน่งโฟลเดอร์จัดเก็บข้อมูลและแม่แบบในเครื่อง:")
        lbl_folders_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #1e293b;")
        lay.addWidget(lbl_folders_title)

        data_dir = storage_service.resolve_data_dir()
        templates_dir = storage_service.get_templates_dir()

        # Row 1: Data folder
        h_data = QHBoxLayout()
        h_data.setSpacing(10)
        lbl_data_path = QLabel(f"<b>ฐานข้อมูล:</b> <span style='color: #475569;'>{data_dir}</span>")
        lbl_data_path.setStyleSheet("font-size: 12px;")
        lbl_data_path.setWordWrap(True)
        h_data.addWidget(lbl_data_path, 1)

        btn_open_data = QPushButton("เปิดโฟลเดอร์ฐานข้อมูล")
        btn_open_data.setObjectName("btnActionSmall")
        btn_open_data.setIcon(get_icon("folder-open", color="#4c1d95", size=14))
        btn_open_data.clicked.connect(lambda: _open_folder_in_explorer(data_dir))
        h_data.addWidget(btn_open_data)
        lay.addLayout(h_data)

        # Row 2: Templates folder
        h_tpl = QHBoxLayout()
        h_tpl.setSpacing(10)
        lbl_tpl_path = QLabel(f"<b>แม่แบบ Word:</b> <span style='color: #475569;'>{templates_dir}</span>")
        lbl_tpl_path.setStyleSheet("font-size: 12px;")
        lbl_tpl_path.setWordWrap(True)
        h_tpl.addWidget(lbl_tpl_path, 1)

        btn_open_tpl = QPushButton("เปิดโฟลเดอร์แม่แบบ")
        btn_open_tpl.setObjectName("btnActionSmall")
        btn_open_tpl.setIcon(get_icon("folder-open", color="#4c1d95", size=14))
        btn_open_tpl.clicked.connect(lambda: _open_folder_in_explorer(templates_dir))
        h_tpl.addWidget(btn_open_tpl)
        lay.addLayout(h_tpl)

        lay.addStretch()
        scroll.setWidget(w)
        return scroll

    # -------------------------------------------------------------------------
    # Tab 2: Changelog Tab
    # -------------------------------------------------------------------------
    def create_changelog_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(14)

        for entry in getattr(constants, "APP_CHANGELOG", []):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1.5px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 12px 14px;
                }
            """)
            v_card = QVBoxLayout(card)
            v_card.setSpacing(8)

            # Header row
            h_card_top = QHBoxLayout()
            h_card_top.setSpacing(8)

            lbl_v = QLabel(f"เวอร์ชัน {entry.get('version')}")
            lbl_v.setStyleSheet("font-size: 14.5px; font-weight: 700; color: #4c1d95;")
            h_card_top.addWidget(lbl_v)

            lbl_d = QLabel(f"•  {entry.get('date')}")
            lbl_d.setStyleSheet("font-size: 12.5px; color: #64748b;")
            h_card_top.addWidget(lbl_d)
            h_card_top.addStretch()
            v_card.addLayout(h_card_top)

            for hl in entry.get("highlights", []):
                r = QHBoxLayout()
                r.setSpacing(8)
                ico = QLabel()
                ico.setPixmap(get_pixmap("check", color="#7c3aed", size=13))
                r.addWidget(ico, 0, Qt.AlignmentFlag.AlignTop)
                lbl = QLabel(hl)
                lbl.setStyleSheet("font-size: 12.5px; color: #334155; line-height: 1.35;")
                lbl.setWordWrap(True)
                r.addWidget(lbl, 1)
                v_card.addLayout(r)

            lay.addWidget(card)

        lay.addStretch()
        scroll.setWidget(w)
        return scroll

    # -------------------------------------------------------------------------
    # Tab 3: System Specifications Tab
    # -------------------------------------------------------------------------
    def create_specs_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)

        lbl_head = QLabel("ข้อมูลจำเพาะระบบและสภาพแวดล้อมการทำงาน (Runtime Environment):")
        lbl_head.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #1e293b;")
        lay.addWidget(lbl_head)

        specs_table = [
            ("ชื่อระบบ", f"{constants.APP_FULL_NAME} ({constants.APP_NAME})"),
            ("หมายเลขเวอร์ชัน", f"{constants.APP_VERSION} (Build: {constants.APP_RELEASE_DATE})"),
            ("ระดับความปลอดภัย", "100% Offline / Air-Gapped (ปลอดภัยสูงสุด ไม่ใช้อินเทอร์เน็ต)"),
            ("มาตรฐานเอกสาร", "แบบพิมพ์กระบวนพิจารณา ๒๒ (ศาลยุติธรรม)"),
            ("Python Runtime", f"Python {platform.python_version()} ({platform.architecture()[0]})"),
            ("UI Framework", "PySide6 (Qt for Python 6.12+)"),
            ("ระบบฐานข้อมูล", "SQLite 3 Engine (ACID Transactional, WAL Concurrency)"),
            ("ระบบปฏิบัติการ", f"{platform.system()} {platform.release()} (Build {platform.version()})"),
            ("ตัวสร้างตัวติดตั้ง", "Inno Setup Compiler 6.7.1 (LZMA2 Ultra Compression)")
        ]

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        v_card = QVBoxLayout(card)
        v_card.setSpacing(6)

        for label, val in specs_table:
            row = QHBoxLayout()
            lbl_k = QLabel(f"•  {label}:")
            lbl_k.setStyleSheet("font-size: 12.5px; font-weight: 600; color: #475569; min-width: 140px;")
            row.addWidget(lbl_k)

            lbl_v = QLabel(val)
            lbl_v.setStyleSheet("font-size: 12.5px; color: #0f172a;")
            lbl_v.setWordWrap(True)
            row.addWidget(lbl_v, 1)

            v_card.addLayout(row)

        lay.addWidget(card)
        lay.addStretch()
        scroll.setWidget(w)
        return scroll
