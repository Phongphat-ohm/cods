"""
Variable Definition Dialog Component
Interactive modal dialog to define and insert template variables
with input type selection and rich date format choices.
"""

import re
from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QDialog, QRadioButton, QButtonGroup, QFrame, QMessageBox
)
from services.icon_service import get_icon
from services.template_variable_service import DATE_FORMAT_STYLES


class VariableDefineDialog(QDialog):
    """
    Interactive modal dialog to define and insert template variables
    with input type selection and rich date format choices.
    """

    def __init__(self, initial_name: str = "", initial_type: str = "date", parent=None):
        super().__init__(parent)
        self.setWindowTitle("กำหนดชิปตัวแปรและประเภทการกรอกข้อมูล - CODS")
        self.resize(500, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: Kanit, sans-serif;
            }
        """)
        self.generated_tag: str = ""
        self.init_ui(initial_name, initial_type)

    def init_ui(self, initial_name: str, initial_type: str = "date"):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header Title
        lbl_head = QLabel("กำหนดตัวแปรและประเภทข้อมูล (Input Type)")
        lbl_head.setStyleSheet("font-size: 17px; font-weight: 700; color: #4c1d95;")
        layout.addWidget(lbl_head)

        lbl_desc = QLabel("เลือกประเภทของตัวแปร เพื่อให้ระบบแสดงช่องกรอกที่เหมาะสม (เช่น ปฏิทินเลือกวัน, ช่องตัวเลข, ตัวเลือก)")
        lbl_desc.setStyleSheet("font-size: 13px; color: #64748b;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # 1. Variable Name
        v_name = QVBoxLayout()
        v_name.setSpacing(4)
        lbl_n = QLabel("1. ชื่อตัวแปร:")
        lbl_n.setStyleSheet("font-size: 13px; font-weight: 600; color: #1e293b;")
        self.txt_var_name = QLineEdit()
        self.txt_var_name.setPlaceholderText("เช่น วันนัดชี้สองสถาน, ดอกเบี้ยร้อยละ, ผลการเจรจา")
        self.txt_var_name.setText(initial_name)
        self.txt_var_name.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 7px 10px;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
            }
            QLineEdit:focus { border-color: #7c3aed; }
        """)
        self.txt_var_name.textChanged.connect(self._update_preview)
        v_name.addWidget(lbl_n)
        v_name.addWidget(self.txt_var_name)
        layout.addLayout(v_name)

        # 2. Input Type Selector
        lbl_t = QLabel("2. เลือกประเภทการกรอกข้อมูล (Input Type):")
        lbl_t.setStyleSheet("font-size: 13px; font-weight: 600; color: #1e293b;")
        layout.addWidget(lbl_t)

        self.btn_group_type = QButtonGroup(self)
        type_grid = QVBoxLayout()
        type_grid.setSpacing(8)

        types = [
            ("date", "📅 วันที่ (Date) - แสดงปฏิทิน พ.ศ., ปุ่มนัดด่วน และแปลงรูปแบบอัตโนมัติ"),
            ("time", "⏰ เวลา (Time) - แสดงเวลานัดทางการศาลและเวลาสำเร็จรูป"),
            ("number", "🔢 ตัวเลข / จำนวนเงิน (Number/Currency) - จัดรูปแบบจุลภาคและเติมคำว่า บาท"),
            ("select", "📋 ตัวเลือกรายการ (Dropdown/Select) - สร้างรายการตัวเลือกให้คลิกเลือกได้สะดวก"),
            ("text", "✏️ ข้อความทั่วไป (Text) - ช่องพิมพ์ข้อความธรรมดา"),
        ]

        self.radio_types = {}
        for idx, (t_id, t_label) in enumerate(types):
            rb = QRadioButton(t_label)
            rb.setStyleSheet("font-size: 13px; color: #334155; padding: 2px;")
            self.btn_group_type.addButton(rb, idx)
            self.radio_types[t_id] = rb
            type_grid.addWidget(rb)

        # Select initial type
        target_rb = self.radio_types.get(initial_type, self.radio_types['date'])
        target_rb.setChecked(True)
        self.btn_group_type.buttonClicked.connect(self._on_type_changed)
        layout.addLayout(type_grid)

        # 3. Dynamic Sub-options frame (Date format or Select options)
        self.opt_frame = QFrame()
        self.opt_frame.setStyleSheet("""
            QFrame {
                background-color: #faf5ff;
                border: 1px solid #e9d5ff;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.opt_layout = QVBoxLayout(self.opt_frame)
        self.opt_layout.setContentsMargins(10, 8, 10, 8)
        self.opt_layout.setSpacing(8)

        # 3.1 Date format controls
        self.date_opt_widget = QWidget()
        date_lay = QVBoxLayout(self.date_opt_widget)
        date_lay.setContentsMargins(0, 0, 0, 0)
        date_lay.setSpacing(6)
        lbl_df = QLabel("เลือกรูปแบบวันที่ต้องการแสดงในเอกสาร:")
        lbl_df.setStyleSheet("font-size: 12.5px; font-weight: 600; color: #581c87;")
        date_lay.addWidget(lbl_df)

        self.cmb_date_format = QComboBox()
        self.cmb_date_format.setStyleSheet("""
            QComboBox {
                font-size: 13px;
                padding: 6px 10px;
                border: 1px solid #c4b5fd;
                border-radius: 6px;
                background: #ffffff;
                color: #4c1d95;
                font-weight: 500;
            }
        """)
        for s_id, s_meta in DATE_FORMAT_STYLES.items():
            self.cmb_date_format.addItem(f"{s_meta['label']} :  {s_meta['example']}", s_id)

        self.cmb_date_format.currentIndexChanged.connect(self._update_preview)
        date_lay.addWidget(self.cmb_date_format)
        self.opt_layout.addWidget(self.date_opt_widget)

        # 3.2 Select options controls
        self.select_opt_widget = QWidget()
        select_lay = QVBoxLayout(self.select_opt_widget)
        select_lay.setContentsMargins(0, 0, 0, 0)
        select_lay.setSpacing(6)
        lbl_so = QLabel("ระบุรายการตัวเลือก (คั่นด้วยเครื่องหมายจุลภาค ','):")
        lbl_so.setStyleSheet("font-size: 12.5px; font-weight: 600; color: #581c87;")
        select_lay.addWidget(lbl_so)

        self.txt_select_options = QLineEdit()
        self.txt_select_options.setPlaceholderText("เช่น เลื่อนนัด, นัดสืบพยาน, ไกล่เกลี่ยสำเร็จ, เจรจาไม่สำเร็จ")
        self.txt_select_options.setText("เลื่อนนัด, นัดสืบพยาน, ไกล่เกลี่ยสำเร็จ")
        self.txt_select_options.textChanged.connect(self._update_preview)
        select_lay.addWidget(self.txt_select_options)
        self.opt_layout.addWidget(self.select_opt_widget)
        self.select_opt_widget.setVisible(False)

        layout.addWidget(self.opt_frame)

        # 4. Live Preview Box
        preview_box = QHBoxLayout()
        preview_box.setSpacing(8)
        lbl_prv_title = QLabel("รหัสชิปที่จะแทรก:")
        lbl_prv_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748b;")
        preview_box.addWidget(lbl_prv_title)

        self.lbl_preview_tag = QLabel("[วันนัด:วันที่:เต็ม]")
        self.lbl_preview_tag.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 700;
                color: #581c87;
                background: #f3e8ff;
                border: 1.5px solid #c4b5fd;
                border-radius: 6px;
                padding: 4px 12px;
            }
        """)
        preview_box.addWidget(self.lbl_preview_tag)
        preview_box.addStretch()
        layout.addLayout(preview_box)

        # Action Buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_cancel = QPushButton("ยกเลิก")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background: #f1f5f9; }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancel)

        btn_insert = QPushButton("แทรกชิปตัวแปรนี้")
        btn_insert.setIcon(get_icon("check", color="#ffffff", size=14))
        btn_insert.setStyleSheet("""
            QPushButton {
                background: #6b21a8;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 18px;
                font-size: 13.5px;
                font-weight: 600;
            }
            QPushButton:hover { background: #7e22ce; }
        """)
        btn_insert.clicked.connect(self.confirm_insert)
        btn_bar.addWidget(btn_insert)

        layout.addLayout(btn_bar)

        self._on_type_changed()
        self._update_preview()

    def _on_type_changed(self):
        is_date = self.radio_types['date'].isChecked()
        is_select = self.radio_types['select'].isChecked()

        self.date_opt_widget.setVisible(is_date)
        self.select_opt_widget.setVisible(is_select)
        self.opt_frame.setVisible(is_date or is_select)

        self._update_preview()

    def _get_current_type_key(self) -> str:
        for t_id, rb in self.radio_types.items():
            if rb.isChecked():
                return t_id
        return 'text'

    def _update_preview(self):
        raw_name = self.txt_var_name.text().strip()
        clean_name = re.sub(r'[^a-zA-Z0-9_\u0e00-\u0e7f]', '', raw_name)
        if not clean_name:
            clean_name = "ชื่อตัวแปร"

        t_key = self._get_current_type_key()

        if t_key == 'date':
            fmt_id = self.cmb_date_format.currentData() or 'full'
            tag = f"[{clean_name}:วันที่:{fmt_id}]"
        elif t_key == 'time':
            tag = f"[{clean_name}:เวลา]"
        elif t_key == 'number':
            tag = f"[{clean_name}:ตัวเลข]"
        elif t_key == 'select':
            opts = self.txt_select_options.text().strip()
            clean_opts = re.sub(r'\s*,\s*', ',', opts) if opts else "ตัวเลือก1,ตัวเลือก2"
            tag = f"[{clean_name}:เลือก:{clean_opts}]"
        else:
            tag = f"[{clean_name}]"

        self.lbl_preview_tag.setText(tag)
        self.generated_tag = tag

    def confirm_insert(self):
        raw_name = self.txt_var_name.text().strip()
        clean_name = re.sub(r'[^a-zA-Z0-9_\u0e00-\u0e7f]', '', raw_name)
        if not clean_name:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อตัวแปร")
            self.txt_var_name.setFocus()
            return

        self._update_preview()
        self.accept()
