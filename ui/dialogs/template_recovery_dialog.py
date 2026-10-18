"""
Template Recovery and Diagnostics Dialog Component
Allows court officers to inspect Word (.docx) templates,
detect missing variables, malformed loop blocks, and syntax errors,
and safely restore pristine default templates bundled with CODS.
"""

import os
import subprocess
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QTextBrowser, QMessageBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from services import storage_service
from services.icon_service import get_icon, get_pixmap, get_app_logo_icon
from services.template_recovery_service import (
    TEMPLATE_DEFINITIONS,
    validate_word_template,
    restore_word_template,
    restore_all_word_templates
)


class TemplateRecoveryDialog(QDialog):
    """Dialog to inspect, diagnose, and restore judicial Word document templates."""

    def __init__(self, parent: Optional[QWidget] = None, initial_tpl_key: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("ตรวจสอบและกู้คืนแม่แบบเอกสาร Word - CODS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(760, 640)
        self.initial_tpl_key = initial_tpl_key or "report"
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(22, 20, 22, 20)
        root_layout.setSpacing(14)

        # Header Title
        head_layout = QHBoxLayout()
        icon_head = QLabel()
        icon_head.setPixmap(get_pixmap("file-text", color="#4c1d95", size=30))
        head_layout.addWidget(icon_head)

        v_head = QVBoxLayout()
        v_head.setSpacing(3)
        lbl_title = QLabel("ตรวจสอบความสมบูรณ์และกู้คืนแม่แบบเอกสาร Word (.docx)")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #4c1d95;")
        lbl_sub = QLabel("หากท่านแก้ไขไฟล์แม่แบบใน Word แล้วโปรแกรมสร้างเอกสารไม่ได้หรือตัวแปรขาดหาย ระบบสามารถตรวจสอบและกู้คืนไฟล์ต้นฉบับได้ทันที")
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("font-size: 13px; color: #64748b; line-height: 1.4;")
        v_head.addWidget(lbl_title)
        v_head.addWidget(lbl_sub)
        head_layout.addLayout(v_head, 1)
        root_layout.addLayout(head_layout)

        # Template Selection Row
        sel_box = QFrame()
        sel_box.setObjectName("selBox")
        sel_box.setStyleSheet("""
            QFrame#selBox {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
        """)
        sel_layout = QHBoxLayout(sel_box)
        sel_layout.setContentsMargins(14, 10, 14, 10)
        sel_layout.setSpacing(12)

        lbl_pick = QLabel("เลือกแม่แบบที่ต้องการตรวจสอบ:")
        lbl_pick.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #1e293b;")
        sel_layout.addWidget(lbl_pick)

        self.cb_templates = QComboBox()
        self.cb_templates.setStyleSheet("""
            QComboBox {
                font-size: 13px;
                padding: 6px 12px;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                background-color: #ffffff;
                color: #0f172a;
                min-width: 280px;
            }
            QComboBox:hover {
                border-color: #94a3b8;
            }
        """)
        for k, v in TEMPLATE_DEFINITIONS.items():
            self.cb_templates.addItem(f"{v['display_name']} ({v['filename']})", k)

        # Set initial combo index
        idx = 0
        for i, k in enumerate(TEMPLATE_DEFINITIONS.keys()):
            if k == self.initial_tpl_key:
                idx = i
                break
        self.cb_templates.setCurrentIndex(idx)
        self.cb_templates.currentIndexChanged.connect(self.run_validation)
        sel_layout.addWidget(self.cb_templates, 1)

        btn_refresh = QPushButton("ตรวจสอบอีกครั้ง")
        btn_refresh.setObjectName("secondaryButtonSmall")
        btn_refresh.setIcon(get_icon("search", color="#4c1d95", size=14))
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #d8b4fe;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12.5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
            }
        """)
        btn_refresh.clicked.connect(self.run_validation)
        sel_layout.addWidget(btn_refresh)

        btn_open_folder = QPushButton("เปิดโฟลเดอร์แม่แบบ")
        btn_open_folder.setObjectName("secondaryButtonSmall")
        btn_open_folder.setIcon(get_icon("folder-open", color="#475569", size=14))
        btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12.5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
        """)
        btn_open_folder.clicked.connect(self.open_template_folder)
        sel_layout.addWidget(btn_open_folder)

        root_layout.addWidget(sel_box)

        # Status Summary Card
        self.status_card = QFrame()
        self.status_card.setObjectName("statusCard")
        self.status_card.setStyleSheet("""
            QFrame#statusCard {
                border-radius: 8px;
                border: 1.5px solid #cbd5e1;
                background-color: #ffffff;
            }
        """)
        status_card_layout = QHBoxLayout(self.status_card)
        status_card_layout.setContentsMargins(16, 12, 16, 12)
        status_card_layout.setSpacing(12)

        self.lbl_status_icon = QLabel()
        status_card_layout.addWidget(self.lbl_status_icon)

        v_st = QVBoxLayout()
        v_st.setSpacing(3)
        self.lbl_status_title = QLabel()
        self.lbl_status_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        self.lbl_status_desc = QLabel()
        self.lbl_status_desc.setWordWrap(True)
        self.lbl_status_desc.setStyleSheet("font-size: 13px; color: #475569;")
        v_st.addWidget(self.lbl_status_title)
        v_st.addWidget(self.lbl_status_desc)
        status_card_layout.addLayout(v_st, 1)

        root_layout.addWidget(self.status_card)

        # Detailed Diagnostic Browser (Rich HTML)
        lbl_detail_head = QLabel("ผลการวิเคราะห์ตัวแปรและโครงสร้างเอกสารอย่างละเอียด:")
        lbl_detail_head.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        root_layout.addWidget(lbl_detail_head)

        self.txt_details = QTextBrowser()
        self.txt_details.setOpenExternalLinks(False)
        self.txt_details.setStyleSheet("""
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Kanit', sans-serif;
                font-size: 13px;
                color: #1e293b;
            }
        """)
        root_layout.addWidget(self.txt_details, 1)

        # Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.btn_restore_current = QPushButton("กู้คืนแม่แบบนี้ (ดึงไฟล์เดิมของระบบ)")
        self.btn_restore_current.setIcon(get_icon("shield", color="#ffffff", size=16))
        self.btn_restore_current.setObjectName("primaryButton")
        self.btn_restore_current.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 13.5px;
                font-weight: 600;
                padding: 9px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
            QPushButton:pressed {
                background-color: #3b0764;
            }
        """)
        self.btn_restore_current.clicked.connect(self.handle_restore_current)
        bottom_bar.addWidget(self.btn_restore_current)

        self.btn_restore_all = QPushButton("กู้คืนแม่แบบทั้งหมด (3 ไฟล์)")
        self.btn_restore_all.setObjectName("secondaryButton")
        self.btn_restore_all.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #d8b4fe;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
            }
        """)
        self.btn_restore_all.clicked.connect(self.handle_restore_all)
        bottom_bar.addWidget(self.btn_restore_all)

        bottom_bar.addStretch()

        btn_close = QPushButton("ปิดหน้าต่าง")
        btn_close.setObjectName("secondaryButton")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13.5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
        """)
        btn_close.clicked.connect(self.accept)
        bottom_bar.addWidget(btn_close)

        root_layout.addLayout(bottom_bar)

        # Initial check
        self.run_validation()

    def get_selected_template_info(self) -> Tuple[str, Dict[str, Any], str]:
        tpl_key = self.cb_templates.currentData()
        tpl_def = TEMPLATE_DEFINITIONS.get(tpl_key, TEMPLATE_DEFINITIONS["report"])
        fname = tpl_def["filename"]
        tpl_dir = storage_service.get_templates_dir()
        file_path = os.path.join(tpl_dir, fname)
        return tpl_key, tpl_def, file_path

    def run_validation(self):
        tpl_key, tpl_def, file_path = self.get_selected_template_info()
        res = validate_word_template(file_path, tpl_key)

        level = res.get("status_level", "error")
        if level == "success":
            self.status_card.setStyleSheet("QFrame#statusCard { border: 1.5px solid #86efac; background-color: #f0fdf4; border-radius: 8px; }")
            self.lbl_status_icon.setPixmap(get_pixmap("status-dot", color="#16a34a", size=18))
            self.lbl_status_title.setText("แม่แบบสมบูรณ์ 100% พร้อมใช้งาน")
            self.lbl_status_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #166534;")
            self.lbl_status_desc.setText(f"ไฟล์ '{res['filename']}' มีโครงสร้างและตัวแปรหลักครบถ้วนตามมาตรฐานศาลยุติธรรม")
        elif level == "warning":
            self.status_card.setStyleSheet("QFrame#statusCard { border: 1.5px solid #fde68a; background-color: #fffbeb; border-radius: 8px; }")
            self.lbl_status_icon.setPixmap(get_pixmap("info", color="#b45309", size=18))
            self.lbl_status_title.setText(f"แม่แบบขาดตัวแปรแนะนำ ({len(res['missing_required'])} ตัวแปร)")
            self.lbl_status_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #b45309;")
            self.lbl_status_desc.setText("สามารถสร้างเอกสารได้ แต่อาจมีข้อมูลบางส่วนไม่ปรากฏลงในเอกสาร Word")
        else:
            self.status_card.setStyleSheet("QFrame#statusCard { border: 1.5px solid #fca5a5; background-color: #fef2f2; border-radius: 8px; }")
            self.lbl_status_icon.setPixmap(get_pixmap("trash", color="#dc2626", size=18))
            self.lbl_status_title.setText("ตรวจพบข้อผิดพลาดในแม่แบบ (สร้างเอกสารไม่ได้)")
            self.lbl_status_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #991b1b;")
            self.lbl_status_desc.setText(res.get("status_message", "กรุณากู้คืนไฟล์แม่แบบต้นฉบับเพื่อแก้ไขปัญหา"))

        # Render HTML Diagnostic Report
        html_parts = []
        html_parts.append(f"<div style='font-family: sans-serif; font-size: 13px;'>")
        html_parts.append(f"<p><b>ตำแหน่งไฟล์ปัจจุบัน:</b> <code>{file_path}</code></p>")

        # 1. Missing Loops (Crucial)
        if res["missing_loops"]:
            html_parts.append("<div style='background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 10px 14px; margin-bottom: 12px; border-radius: 4px;'>")
            html_parts.append("<b style='color: #991b1b; font-size: 14px;'>โครงสร้างวนซ้ำหลักที่ขาดหายไป (Critical Loop Blocks):</b><br>")
            html_parts.append("<p style='margin: 4px 0; color: #7f1d1d;'>แม่แบบจำเป็นต้องมีบล็อกเหล่านี้เพื่อให้ระบบเขียนเนื้อหาลงในไฟล์ Word:</p>")
            html_parts.append("<ul style='margin: 6px 0; padding-left: 20px; color: #991b1b;'>")
            for loop in res["missing_loops"]:
                html_parts.append(f"<li><b>{loop['start_tag']} ... {loop['end_tag']}</b> — <span style='color: #b91c1c;'>{loop['issue']}</span><br>"
                                  f"<span style='color: #4b5563; font-size: 12px;'>• ผลกระทบ: {loop['description']}</span></li>")
            html_parts.append("</ul></div>")

        # 2. Syntax Errors
        if res["syntax_errors"]:
            html_parts.append("<div style='background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 10px 14px; margin-bottom: 12px; border-radius: 4px;'>")
            html_parts.append("<b style='color: #991b1b; font-size: 14px;'>ข้อผิดพลาดทางไวยากรณ์ (Syntax Errors):</b>")
            html_parts.append("<ul style='margin: 6px 0; padding-left: 20px; color: #991b1b;'>")
            for err in res["syntax_errors"]:
                html_parts.append(f"<li>{err}</li>")
            html_parts.append("</ul></div>")

        # 3. Missing Required Variables
        if res["missing_required"]:
            html_parts.append("<div style='background-color: #fef3c7; border-left: 4px solid #d97706; padding: 10px 14px; margin-bottom: 12px; border-radius: 4px;'>")
            html_parts.append(f"<b style='color: #92400e; font-size: 14px;'>ตัวแปรที่ยังขาดหายไปในแม่แบบ ({len(res['missing_required'])} ตัวแปร):</b>")
            html_parts.append("<table style='width: 100%; border-collapse: collapse; margin-top: 8px;'>")
            html_parts.append("<tr style='background-color: #fde68a; color: #78350f;'><th style='text-align: left; padding: 6px 8px;'>ชื่อตัวแปรที่ขาด</th><th style='text-align: left; padding: 6px 8px;'>หน้าที่ / ข้อมูลที่ใช้</th></tr>")
            for var in res["missing_required"]:
                html_parts.append(f"<tr style='border-bottom: 1px solid #fde68a;'>"
                                  f"<td style='padding: 6px 8px; font-weight: bold; color: #b45309;'><code>{var['tag']}</code></td>"
                                  f"<td style='padding: 6px 8px; color: #78350f;'>{var['description']}</td></tr>")
            html_parts.append("</table></div>")

        # 4. Detected Variables (Green)
        if res["detected_tags"]:
            html_parts.append("<div style='background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 14px; border-radius: 6px;'>")
            html_parts.append(f"<b style='color: #334155;'>ตัวแปรและคำสั่งที่ตรวจพบในไฟล์นี้ ({len(res['detected_tags'])} รายการ):</b><br>")
            tags_html = " ".join([f"<span style='display: inline-block; background-color: #ede9fe; color: #4c1d95; padding: 2px 7px; border-radius: 4px; margin: 3px 2px; font-size: 12px;'><code>[{t}]</code></span>" for t in res["detected_tags"]])
            html_parts.append(f"<div style='margin-top: 6px;'>{tags_html}</div>")
            html_parts.append("</div>")

        html_parts.append("</div>")
        self.txt_details.setHtml("".join(html_parts))

    def handle_restore_current(self):
        tpl_key, tpl_def, file_path = self.get_selected_template_info()
        fname = tpl_def["filename"]

        reply = QMessageBox.question(
            self, "ยืนยันการกู้คืนแม่แบบ",
            f"ท่านต้องการกู้คืนแม่แบบ '{fname}' กลับสู่ค่าเริ่มต้นของโปรแกรมใช่หรือไม่?\n\n"
            f"• ระบบจะสำรองไฟล์ปัจจุบันที่ท่านเคยแก้ไขไว้ในโฟลเดอร์ templates/backup/\n"
            f"• ระบบจะดึงไฟล์แม่แบบต้นฉบับ 100% มาเขียนแทนที่เพื่อให้สร้างเอกสารได้ตามปกติ",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        ok, msg, bkp = restore_word_template(fname)
        if ok:
            bkp_info = f"\n\n(ได้สำรองไฟล์เดิมไว้ที่: {os.path.basename(bkp)})" if bkp else ""
            QMessageBox.information(self, "สำเร็จ", msg + bkp_info)
            self.run_validation()
        else:
            QMessageBox.critical(self, "ข้อผิดพลาด", msg)

    def handle_restore_all(self):
        reply = QMessageBox.question(
            self, "ยืนยันการกู้คืนแม่แบบทั้งหมด",
            "ท่านต้องการกู้คืนแม่แบบ Word ทั้งหมด (3 ฉบับ) กลับสู่ค่าเริ่มต้นของโปรแกรมใช่หรือไม่?\n\n"
            "ระบบจะสำรองไฟล์เดิมไว้ในโฟลเดอร์ templates/backup/ ก่อนทำการกู้คืน",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        res = restore_all_word_templates()
        success_list = [f for f, (ok, _, _) in res.items() if ok]
        fail_list = [f for f, (ok, _, _) in res.items() if not ok]

        msg_lines = [f"กู้คืนสำเร็จ {len(success_list)} ไฟล์"]
        if fail_list:
            msg_lines.append(f"เกิดข้อผิดพลาด {len(fail_list)} ไฟล์: {', '.join(fail_list)}")

        QMessageBox.information(self, "ผลการกู้คืน", "\n".join(msg_lines))
        self.run_validation()

    def open_template_folder(self):
        tpl_dir = storage_service.get_templates_dir()
        if os.path.exists(tpl_dir):
            if os.name == 'nt':
                os.startfile(tpl_dir)
            else:
                subprocess.Popen(['xdg-open', tpl_dir])
        else:
            QMessageBox.warning(self, "แจ้งเตือน", f"ไม่พบโฟลเดอร์: {tpl_dir}")
