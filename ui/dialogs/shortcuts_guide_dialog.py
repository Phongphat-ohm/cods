"""
Shortcuts Guide Dialog Component
Dialog displaying the comprehensive keyboard shortcuts cheat sheet.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from services.icon_service import get_pixmap, get_app_logo_icon


class ShortcutsGuideDialog(QDialog):
    """Dialog displaying the comprehensive keyboard shortcuts cheat sheet."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("คู่มือคีย์ลัดการทำงานระบบศาล (CODS Shortcuts) - CODS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(760, 560)
        self.setMinimumHeight(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        # Header Bar
        top_bar = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("help-circle", color="#4c1d95", size=24))
        top_bar.addWidget(icon_lbl)

        lbl_title = QLabel("คู่มือคีย์ลัดการทำงาน (Keyboard Shortcuts Guide)")
        lbl_title.setStyleSheet("font-size: 19px; font-weight: 700; color: #4c1d95;")
        top_bar.addWidget(lbl_title)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        lbl_desc = QLabel(
            "ระบบได้รับการออกแบบให้รองรับการทำงานด้วยแป้นพิมพ์เป็นหลัก (Keyboard-First) "
            "เพื่อความรวดเร็วและความคล่องตัวสูงสุดของเจ้าหน้าที่ศาลยุติธรรม"
        )
        lbl_desc.setStyleSheet("font-size: 13px; color: #475569; line-height: 1.4;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # Shortcuts Content Widget
        content_widget = QWidget()
        f_layout = QVBoxLayout(content_widget)
        f_layout.setContentsMargins(16, 12, 16, 16)
        f_layout.setSpacing(10)

        shortcuts_data = [
            ("การนำทางและขั้นตอนด้วย CTRL & แป้นพิมพ์ (Workflow Navigation)", [
                ("Ctrl + H", "กลับสู่หน้าหลัก / แดชบอร์ด (Dashboard)"),
                ("Ctrl + 1 / 2 / 3 / 4", "สลับไปยังขั้นตอนที่ 1 (เลือกไฟล์), 2 (เลือกคดี), 3 (เลือกประเภทเอกสาร), 4 (จัดทำเอกสาร)"),
                ("PageDown (PgDn)", "ไปขั้นตอนถัดไป / เลื่อนไปยัง Section ถัดไป"),
                ("PageUp (PgUp)", "ย้อนกลับขั้นตอนก่อนหน้า / Section ก่อนหน้า"),
                ("Ctrl + O", "เปิดหน้าต่างเลือกไฟล์ Excel ตารางนัด"),
                ("Ctrl + F", "กระโดดไปยังช่องค้นหาคดีในขั้นตอนตารางคดี"),
            ]),
            ("การกรอกฟอร์ม & Autocomplete", [
                ("Focus / คลิกเข้าช่อง", "แสดงรายการคำแนะนำ (Dropdown) ทันทีอัตโนมัติ"),
                ("ลูกศรลง / ขึ้น (↓ / ↑)", "เลื่อนแถบเลือกรายการใน Dropdown คำแนะนำ"),
                ("Enter หรือ Tab", "ยืนยันการเลือกและเติมข้อความลงในช่องทันที"),
                ("Escape (Esc)", "ปิดหน้าต่างรายการคำแนะนำ"),
            ]),
            ("การสร้างเอกสาร & คีย์ลัดจัดการข้อมูล (Document Actions)", [
                ("Ctrl + S หรือ F5", "สั่งสร้างรายงานกระบวนพิจารณา Word (.docx) ทันที"),
                ("Ctrl + T", "เปิดคลังจัดการ Template ย่อหน้าส่วนตัว"),
                ("Ctrl + B", "เปิดหน้าต่างจัดการคู่องค์คณะผู้พิพากษา"),
                ("F12 หรือ Ctrl + I", "เปิดหน้าต่างเกี่ยวกับโปรแกรม (About & Version)"),
                ("F1", "เปิดคู่มือสรุปคีย์ลัดนี้"),
            ])
        ]

        for category, items in shortcuts_data:
            cat_lbl = QLabel(category)
            cat_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #4c1d95; margin-top: 6px;")
            f_layout.addWidget(cat_lbl)

            for key, desc in items:
                row = QHBoxLayout()
                row.setSpacing(12)

                badge = QLabel(key)
                badge.setStyleSheet(
                    "background-color: #f5f3ff; color: #4c1d95; font-weight: 600; "
                    "font-size: 12px; padding: 4px 10px; border: 1px solid #ddd6fe; border-radius: 4px; min-width: 140px;"
                )
                badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
                row.addWidget(badge)

                desc_lbl = QLabel(desc)
                desc_lbl.setStyleSheet("font-size: 13px; color: #334155;")
                row.addWidget(desc_lbl)
                row.addStretch()
                f_layout.addLayout(row)

        f_layout.addStretch()

        # ScrollArea to ensure responsiveness on 768p/720p or 125% scaling
        scroll_area = QScrollArea()
        scroll_area.setObjectName("shortcutsScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea#shortcutsScrollArea {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
            }
            QScrollArea#shortcutsScrollArea > QWidget > QWidget {
                background-color: #ffffff;
            }
        """)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area, 1)

        # Close button
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        btn_close = QPushButton("ปิดหน้าต่าง")
        btn_close.setObjectName("primaryButton")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 13.5px;
                font-weight: 600;
                padding: 8px 24px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
            QPushButton:pressed {
                background-color: #3b0764;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
                color: #e2e8f0;
            }
        """)
        btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(btn_close)
        layout.addLayout(btn_bar)
