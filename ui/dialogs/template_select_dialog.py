"""
Template Select Dialog Component
Quickly search, preview, and select a paragraph template.
"""

import re
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QComboBox, QFrame, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from services import storage_service
from services.icon_service import get_icon, get_pixmap, get_app_logo_icon
from services.template_variable_service import parse_variable_tag
from ui.components.template_chip_highlighter import format_text_as_chips_html


class TemplateSelectDialog(QDialog):
    """Dialog to quickly search, preview, and select a paragraph template."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("เลือก Template ข้อความกระบวนพิจารณา - CODS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(880, 600)
        self.selected_content: Optional[str] = None
        self.templates = storage_service.load_templates()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header & Manage button
        top_bar = QHBoxLayout()
        v_title = QVBoxLayout()
        v_title.setSpacing(2)
        lbl_title = QLabel("คลัง Template ข้อความกระบวนพิจารณา")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #4c1d95;")
        lbl_sub = QLabel("เลือกข้อความสำเร็จรูปเพื่อนำไปแทรกในย่อหน้ากระบวนพิจารณา")
        lbl_sub.setStyleSheet("font-size: 13px; color: #64748b;")
        v_title.addWidget(lbl_title)
        v_title.addWidget(lbl_sub)
        top_bar.addLayout(v_title)
        top_bar.addStretch()

        # Prominent Add/Manage Template Button
        self.btn_manage = QPushButton("จัดการ / สร้าง Template ใหม่")
        self.btn_manage.setObjectName("primaryButton")
        self.btn_manage.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 13.5px;
                font-weight: 600;
                padding: 8px 16px;
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
        self.btn_manage.setIcon(get_icon("settings", color="#ffffff", size=15))
        self.btn_manage.clicked.connect(self.open_manager)
        top_bar.addWidget(self.btn_manage)
        layout.addLayout(top_bar)

        # Search Bar & Filter
        search_bar = QHBoxLayout()
        search_bar.setSpacing(10)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("ค้นหา Template (ชื่อ หรือ ข้อความ)...")
        self.txt_search.textChanged.connect(self.filter_templates)
        search_bar.addWidget(self.txt_search, 2)

        self.cmb_category = QComboBox()
        self.cmb_category.addItem("ทุกหมวดหมู่")
        cats = sorted(list(set(t.get("category", "ทั่วไป") for t in self.templates)))
        for c in cats:
            if c:
                self.cmb_category.addItem(c)
        self.cmb_category.currentTextChanged.connect(self.filter_templates)
        search_bar.addWidget(self.cmb_category, 1)
        layout.addLayout(search_bar)

        # Main Splitter: Left List, Right Preview
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left list
        left_widget = QFrame()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        lbl_list = QLabel("รายการ Template:")
        lbl_list.setStyleSheet("font-size: 14px; font-weight: 600; color: #334155;")
        left_layout.addWidget(lbl_list)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.on_item_selected)
        self.list_widget.itemDoubleClicked.connect(lambda: self.accept_selection())
        left_layout.addWidget(self.list_widget)
        splitter.addWidget(left_widget)

        # Right preview
        right_widget = QFrame()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        lbl_preview = QLabel("ตัวอย่างข้อความ:")
        lbl_preview.setStyleSheet("font-size: 14px; font-weight: 600; color: #334155;")
        right_layout.addWidget(lbl_preview)

        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setStyleSheet("background-color: #f8fafc; font-size: 15px; line-height: 1.6; color: #0f172a;")
        right_layout.addWidget(self.txt_preview)

        # Real-time detected variables badge
        self.lbl_preview_vars = QLabel()
        self.lbl_preview_vars.setStyleSheet("font-size: 13px; color: #4c1d95; background: #f5f3ff; border: 1px solid #ddd6fe; border-radius: 6px; padding: 6px 10px; font-weight: 500;")
        self.lbl_preview_vars.setVisible(False)
        right_layout.addWidget(self.lbl_preview_vars)

        splitter.addWidget(right_widget)
        splitter.setSizes([340, 520])
        layout.addWidget(splitter)

        # Bottom buttons
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

        self.btn_insert = QPushButton("ใช้ Template นี้")
        self.btn_insert.setObjectName("primaryButton")
        self.btn_insert.setIcon(get_icon("check", color="#ffffff", size=15))
        self.btn_insert.setStyleSheet("""
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
        self.btn_insert.clicked.connect(self.accept_selection)
        btn_bar.addWidget(self.btn_insert)

        layout.addLayout(btn_bar)
        self.refresh_list()

    def refresh_list(self):
        self.templates = storage_service.load_templates()
        self.filter_templates()

    def filter_templates(self):
        q = self.txt_search.text().strip().lower()
        selected_cat = self.cmb_category.currentText()

        self.list_widget.clear()
        self.filtered_templates = []

        for tpl in self.templates:
            title = tpl.get("title", "")
            content = tpl.get("content", "")
            cat = tpl.get("category", "ทั่วไป")

            if selected_cat != "ทุกหมวดหมู่" and cat != selected_cat:
                continue

            if q and (q not in title.lower() and q not in content.lower()):
                continue

            self.filtered_templates.append(tpl)
            item = QListWidgetItem(f"[{cat}] {title}")
            item.setData(Qt.ItemDataRole.UserRole, tpl)
            self.list_widget.addItem(item)

        if self.filtered_templates:
            self.list_widget.setCurrentRow(0)
        else:
            self.txt_preview.clear()
            if hasattr(self, 'lbl_preview_vars'):
                self.lbl_preview_vars.setVisible(False)

    def on_item_selected(self, row: int):
        if 0 <= row < len(self.filtered_templates):
            tpl = self.filtered_templates[row]
            cnt = tpl.get("content", "")
            self.txt_preview.setHtml(format_text_as_chips_html(cnt))
            matches = re.findall(r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]]+?)\s*\]|\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', cnt)
            vars_found = []
            for m1, m2, m3 in matches:
                t = (m1 or m2 or m3).strip()
                t = re.sub(r'^[\U0001f3f7\ufe0f\s]+', '', t).strip()
                if t and not t.startswith(('#', '/')):
                    base_n = parse_variable_tag(t)['name'] or t
                    vars_found.append(base_n)
            if vars_found:
                unique_vars = sorted(list(set(vars_found)))
                chips_display = "   •   ".join(unique_vars)
                self.lbl_preview_vars.setText(f"ตรวจพบตัวแปร {len(unique_vars)} รายการ: {chips_display}")
                self.lbl_preview_vars.setVisible(True)
            else:
                self.lbl_preview_vars.setVisible(False)
        else:
            self.txt_preview.clear()
            if hasattr(self, 'lbl_preview_vars'):
                self.lbl_preview_vars.setVisible(False)

    def accept_selection(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.filtered_templates):
            self.selected_content = self.filtered_templates[row].get("content", "")
            self.accept()
        else:
            QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือก Template ที่ต้องการ")

    def open_manager(self):
        from ui.dialogs.template_manager_dialog import TemplateManagerDialog
        dlg = TemplateManagerDialog(self)
        dlg.exec()
        self.refresh_list()
