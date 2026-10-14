"""
Save Template Modal Component
Quick modal to save paragraph text as a template directly from a paragraph card.
"""
import re
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from services import storage_service
from services.docx_service import validate_template_variable
from services.icon_service import get_icon, get_app_logo_icon


class SaveTemplateModal(QDialog):
    """Quick modal to save paragraph text as a template directly from a paragraph card."""

    def __init__(self, content: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("บันทึกเป็น Template ส่วนตัว - JADS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(560, 480)
        self.content = content
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        lbl_header = QLabel("บันทึกข้อความนี้เป็น Template ส่วนตัว")
        lbl_header.setStyleSheet("font-size: 18px; font-weight: 700; color: #4c1d95;")
        layout.addWidget(lbl_header)

        lbl_name = QLabel("ชื่อ Template:")
        lbl_name.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        layout.addWidget(lbl_name)

        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("เช่น รายงานกระบวนพิจารณาแบบพิเศษ")
        layout.addWidget(self.txt_title)

        lbl_cat = QLabel("หมวดหมู่:")
        lbl_cat.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        layout.addWidget(lbl_cat)

        self.txt_category = QLineEdit()
        self.txt_category.setText("ส่วนตัว")
        layout.addWidget(self.txt_category)

        lbl_preview = QLabel("ข้อความที่จะบันทึก:")
        lbl_preview.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        layout.addWidget(lbl_preview)

        self.txt_content = QTextEdit()
        self.txt_content.setPlainText(self.content)
        self.txt_content.setMinimumHeight(110)
        layout.addWidget(self.txt_content)

        # Quick Tip Box
        tip_frame = QFrame()
        tip_frame.setObjectName("quickTipFrame")
        tip_frame.setStyleSheet("""
            QFrame#quickTipFrame {
                background-color: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 6px;
                padding: 6px 10px;
            }
        """)
        tip_layout = QVBoxLayout(tip_frame)
        tip_layout.setContentsMargins(8, 6, 8, 6)
        tip_layout.setSpacing(3)

        lbl_tip = QLabel("<b>คำแนะนำตัวแปร:</b> สามารถใช้ <code>{{ชื่อตัวแปร}}</code> ในข้อความเพื่อสร้างช่องกรอกข้อมูลอัตโนมัติได้ (ห้ามมีช่องว่างในชื่อตัวแปร)")
        lbl_tip.setTextFormat(Qt.TextFormat.RichText)
        lbl_tip.setStyleSheet("font-size: 12px; color: #166534;")
        lbl_tip.setWordWrap(True)
        tip_layout.addWidget(lbl_tip)
        layout.addWidget(tip_frame)

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

        btn_save = QPushButton("บันทึก Template")
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
        btn_save.clicked.connect(self.save)
        btn_bar.addWidget(btn_save)

        layout.addLayout(btn_bar)

    def save(self):
        title = self.txt_title.text().strip()
        cat = self.txt_category.text().strip() or "ส่วนตัว"
        content = self.txt_content.toPlainText().strip()
        if not title:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อ Template")
            self.txt_title.setFocus()
            return
        if not content:
            QMessageBox.warning(self, "แจ้งเตือน", "เนื้อหาข้อความว่างเปล่า")
            self.txt_content.setFocus()
            return

        # Check for unclosed template braces
        if content.count('{{') != content.count('}}'):
            QMessageBox.warning(
                self, "ไวยากรณ์ตัวแปรไม่สมบูรณ์",
                "พบเครื่องหมาย {{ หรือ }} ไม่ครบคู่ในเนื้อหา Template\nกรุณาตรวจสอบและปิดวงเล็บให้สมบูรณ์ก่อนบันทึก"
            )
            self.txt_content.setFocus()
            return

        # Validate variables and forbidden keywords
        matches = re.findall(r'\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', content)
        for m1, m2 in matches:
            tag = (m1 or m2).strip()
            if not tag:
                QMessageBox.warning(
                    self, "ไวยากรณ์ตัวแปรไม่ถูกต้อง",
                    "พบวงเล็บตัวแปรว่างเปล่า '{{}}' ในเนื้อหา\nกรุณาระบุชื่อตัวแปรหรือลบวงเล็บออกก่อนบันทึก"
                )
                return
            is_valid, err_msg = validate_template_variable(tag)
            if not is_valid:
                QMessageBox.warning(
                    self, "พบคำต้องห้ามใน Template",
                    f"ไม่สามารถบันทึก Template ได้เนื่องจากพบปัญหาในตัวแปร:\n\n• {err_msg}\n\nกรุณาแก้ไขก่อนบันทึก"
                )
                return

        storage_service.add_template(title, content, cat)
        QMessageBox.information(self, "สำเร็จ", f"บันทึก Template '{title}' เรียบร้อยแล้ว")
        self.accept()
