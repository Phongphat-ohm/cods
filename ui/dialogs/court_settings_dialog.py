"""
Court Settings Dialog Component
Dialog to configure and save default court name.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox
)
from services import storage_service
from services.icon_service import get_icon, get_app_logo_icon


class CourtSettingsDialog(QDialog):
    """Dialog to configure and save default court name."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("ตั้งค่าชื่อศาลเริ่มต้น - CODS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        # Header
        lbl_title = QLabel("ตั้งค่าชื่อศาลเริ่มต้น (Default Court)")
        lbl_title.setStyleSheet("font-size: 19px; font-weight: 700; color: #4c1d95;")
        layout.addWidget(lbl_title)

        lbl_desc = QLabel(
            "กำหนดชื่อศาลเริ่มต้นประจำเครื่อง ระบบจะนำชื่อนี้ไปแสดงในแบบฟอร์มรายงานกระบวนพิจารณาโดยอัตโนมัติ "
            "ทุกครั้งที่เปิดโปรแกรมหรือเลือกคดีความจากตาราง (ไม่ต้องพิมพ์ใหม่ทุกครั้ง)"
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 13px; color: #475569; line-height: 1.5;")
        layout.addWidget(lbl_desc)

        # Input card
        frame = QFrame()
        frame.setObjectName("courtSettingsFrame")
        frame.setStyleSheet("""
            QFrame#courtSettingsFrame {
                background-color: #f8fafc;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
            }
        """)
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(16, 14, 16, 14)
        f_layout.setSpacing(10)

        lbl_input = QLabel("ชื่อศาลที่ต้องการใช้เป็นค่าเริ่มต้น:")
        lbl_input.setStyleSheet("font-size: 14px; font-weight: 600; color: #0f172a;")
        f_layout.addWidget(lbl_input)

        self.txt_court = QLineEdit()
        self.txt_court.setPlaceholderText("เช่น ศาลแพ่ง, ศาลแพ่งกรุงเทพใต้, ศาลจังหวัดนนทบุรี")
        current_court = storage_service.get_default_court_name()
        self.txt_court.setText(current_court)
        f_layout.addWidget(self.txt_court)

        # Quick preset buttons
        lbl_presets = QLabel("เลือกด่วนจากรายการยอดนิยม:")
        lbl_presets.setStyleSheet("font-size: 12.5px; color: #64748b; font-weight: 500;")
        f_layout.addWidget(lbl_presets)

        common_courts = [
            ["ศาลแพ่ง", "ศาลแพ่งกรุงเทพใต้", "ศาลแพ่งธนบุรี"],
            ["ศาลจังหวัดนนทบุรี", "ศาลแขวงดอนเมือง"]
        ]
        preset_vbox = QVBoxLayout()
        preset_vbox.setSpacing(6)
        for row_courts in common_courts:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            for c in row_courts:
                btn_p = QPushButton(c)
                btn_p.setObjectName("secondaryButtonSmall")
                btn_p.setStyleSheet("""
                    QPushButton {
                        background-color: #ffffff;
                        color: #4c1d95;
                        border: 1px solid #ddd6fe;
                        border-radius: 5px;
                        font-size: 12px;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        background-color: #f5f3ff;
                        border-color: #c4b5fd;
                    }
                    QPushButton:pressed {
                        background-color: #ede9fe;
                    }
                    QPushButton:disabled {
                        color: #94a3b8;
                        border-color: #e2e8f0;
                        background-color: #f8fafc;
                    }
                """)
                btn_p.clicked.connect(lambda _, name=c: self.txt_court.setText(name))
                row_layout.addWidget(btn_p)
            row_layout.addStretch()
            preset_vbox.addLayout(row_layout)
        f_layout.addLayout(preset_vbox)

        # Online Platform Frame Section
        lbl_platform_sep = QFrame()
        lbl_platform_sep.setFrameShape(QFrame.Shape.HLine)
        lbl_platform_sep.setStyleSheet("color: #e2e8f0; margin-top: 10px; margin-bottom: 8px;")
        f_layout.addWidget(lbl_platform_sep)

        lbl_platform_title = QLabel("ระบบการประชุมออนไลน์เริ่มต้น (Default Online Meeting Platform):")
        lbl_platform_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #0f172a;")
        f_layout.addWidget(lbl_platform_title)

        self.txt_platform = QLineEdit()
        self.txt_platform.setPlaceholderText("เช่น Google Meet, Zoom, Cisco Webex, Microsoft Teams")
        current_plat = storage_service.get_default_online_platform()
        self.txt_platform.setText(current_plat)
        f_layout.addWidget(self.txt_platform)

        lbl_plat_presets = QLabel("เลือกด่วนจากระบบยอดนิยม:")
        lbl_plat_presets.setStyleSheet("font-size: 12.5px; color: #64748b; font-weight: 500;")
        f_layout.addWidget(lbl_plat_presets)

        h_plat_presets = QHBoxLayout()
        h_plat_presets.setSpacing(8)
        for plat_name in ["Google Meet", "Zoom", "Cisco Webex", "Microsoft Teams"]:
            btn_plat = QPushButton(plat_name)
            btn_plat.setObjectName("secondaryButtonSmall")
            btn_plat.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #4c1d95;
                    border: 1px solid #ddd6fe;
                    border-radius: 5px;
                    font-size: 12px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background-color: #f5f3ff;
                    border-color: #c4b5fd;
                }
                QPushButton:pressed {
                    background-color: #ede9fe;
                }
            """)
            btn_plat.clicked.connect(lambda _, p=plat_name: self.txt_platform.setText(p))
            h_plat_presets.addWidget(btn_plat)
        h_plat_presets.addStretch()
        f_layout.addLayout(h_plat_presets)

        layout.addWidget(frame)

        # Buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_cancel = QPushButton("ยกเลิก")
        btn_cancel.setObjectName("secondaryButton")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #1e293b;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 13.5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancel)

        btn_save = QPushButton("บันทึกการตั้งค่า")
        btn_save.setObjectName("primaryButton")
        btn_save.setIcon(get_icon("save", color="#ffffff", size=15))
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 13.5px;
                font-weight: 600;
                padding: 8px 18px;
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
        btn_save.clicked.connect(self.save_court)
        btn_bar.addWidget(btn_save)

        layout.addLayout(btn_bar)

    def save_court(self):
        c_name = self.txt_court.text().strip()
        p_name = self.txt_platform.text().strip() or "Google Meet"
        storage_service.set_default_court_name(c_name)
        storage_service.set_default_online_platform(p_name)
        
        info_lines = []
        if c_name:
            info_lines.append(f"ชื่อศาลเริ่มต้น: {c_name}")
        else:
            info_lines.append("ชื่อศาลเริ่มต้น: (ค่าว่าง)")
        info_lines.append(f"ระบบประชุมออนไลน์เริ่มต้น: {p_name}")

        QMessageBox.information(
            self, "บันทึกสำเร็จ",
            "บันทึกการตั้งค่าเรียบร้อยแล้ว:\n" + "\n".join(info_lines) +
            "\n\nระบบจะนำไปแสดงในแบบฟอร์มโดยอัตโนมัติ"
        )
        self.accept()

