"""
Template Manager Dialog Component
Full management dialog to Add, Edit, Delete paragraph templates,
complete with syntax validation, forbidden keyword checks, and an informative variable creation Tip.
"""
import re
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QListWidgetItem, QFrame,
    QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
from services import storage_service
from services.docx_service import validate_template_variable, SYSTEM_RESERVED_VARIABLES
from services.icon_service import get_icon, get_pixmap, get_app_logo_icon
from ui.components.draggable_list import DraggableListWidget


class TemplateManagerDialog(QDialog):
    """Full management dialog to Add, Edit, Delete paragraph templates."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("จัดการ Template ข้อความกระบวนพิจารณา - JADS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(980, 680)
        self.templates = storage_service.load_templates()
        self.current_tpl_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header bar
        top_bar = QHBoxLayout()
        v_title = QVBoxLayout()
        v_title.setSpacing(2)
        lbl_title = QLabel("จัดการและแก้ไข Template ข้อความกระบวนพิจารณา")
        lbl_title.setStyleSheet("font-size: 19px; font-weight: 700; color: #4c1d95;")
        lbl_sub = QLabel("เพิ่ม แก้ไข หรือลบข้อความสำเร็จรูป พร้อมกำหนดตัวแปร {{...}} เพื่อให้ระบบสร้างช่องกรอกอัตโนมัติ")
        lbl_sub.setStyleSheet("font-size: 13px; color: #64748b;")
        v_title.addWidget(lbl_title)
        v_title.addWidget(lbl_sub)
        top_bar.addLayout(v_title)
        top_bar.addStretch()

        # High-contrast, highly-visible Add Template button
        self.btn_new = QPushButton("สร้าง Template ใหม่")
        self.btn_new.setObjectName("primaryButton")
        self.btn_new.setIcon(get_icon("plus", color="#ffffff", size=15))
        self.btn_new.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 14px;
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
            QPushButton:disabled {
                background-color: #94a3b8;
                color: #e2e8f0;
            }
        """)
        self.btn_new.clicked.connect(self.prepare_new_template)
        top_bar.addWidget(self.btn_new)
        layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Column: List of templates
        left_box = QFrame()
        left_box.setObjectName("templateListFrame")
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        self.txt_filter = QLineEdit()
        self.txt_filter.setPlaceholderText("ค้นหา Template...")
        self.txt_filter.addAction(get_icon("search", color="#94a3b8", size=15), QLineEdit.ActionPosition.LeadingPosition)
        self.txt_filter.textChanged.connect(self.filter_list)
        left_layout.addWidget(self.txt_filter)

        self.list_widget = DraggableListWidget()
        self.list_widget.setToolTip("คลิกค้างแล้วลากรายการเพื่อสลับลำดับ (Drag & Drop) — ระบบบันทึกลำดับอัตโนมัติ")
        self.list_widget.currentRowChanged.connect(self.on_select_template)
        self.list_widget.order_changed.connect(self.on_order_changed)
        left_layout.addWidget(self.list_widget)

        splitter.addWidget(left_box)

        # Right Column: Editor Form
        right_box = QFrame()
        right_box.setObjectName("editorBox")
        right_box.setStyleSheet("""
            QFrame#editorBox {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
        """)
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(18, 16, 18, 16)
        right_layout.setSpacing(12)

        lbl_edit_title = QLabel("รายละเอียด Template")
        lbl_edit_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0f172a;")
        right_layout.addWidget(lbl_edit_title)

        form_meta = QHBoxLayout()
        v_name = QVBoxLayout()
        v_name.setSpacing(4)
        lbl_t = QLabel("ชื่อ Template:")
        lbl_t.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        self.edt_title = QLineEdit()
        self.edt_title.setPlaceholderText("ระบุชื่อหัวข้อ Template เช่น ไกล่เกลี่ยสำเร็จ, เลื่อนนัดพร้อม")
        v_name.addWidget(lbl_t)
        v_name.addWidget(self.edt_title)
        form_meta.addLayout(v_name, 2)

        v_cat = QVBoxLayout()
        v_cat.setSpacing(4)
        lbl_c = QLabel("หมวดหมู่:")
        lbl_c.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        self.edt_category = QLineEdit()
        self.edt_category.setPlaceholderText("เช่น ทั่วไป, นัดพร้อม, คำพิพากษา")
        v_cat.addWidget(lbl_c)
        v_cat.addWidget(self.edt_category)
        form_meta.addLayout(v_cat, 1)
        right_layout.addLayout(form_meta)

        lbl_body = QLabel("เนื้อหาข้อความกระบวนพิจารณา:")
        lbl_body.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        right_layout.addWidget(lbl_body)

        self.edt_content = QTextEdit()
        self.edt_content.setPlaceholderText("พิมพ์เนื้อหาข้อความกระบวนพิจารณา... ท่านสามารถใส่ตัวแปรได้ เช่น {{หมายเหตุ}} หรือ {{จำนวนเงิน}} เพื่อให้ระบบสร้างช่องกรอกข้อมูลอัตโนมัติ")
        self.edt_content.setMinimumHeight(140)
        right_layout.addWidget(self.edt_content)

        # Real-time Variable Validation Indicator
        self.lbl_var_validation = QLabel()
        self.lbl_var_validation.setWordWrap(True)
        self.lbl_var_validation.setStyleSheet("font-size: 13px; padding: 7px 12px; border-radius: 6px;")
        self.lbl_var_validation.setVisible(False)
        right_layout.addWidget(self.lbl_var_validation)
        self.edt_content.textChanged.connect(self.validate_content_variables)

        # -------------------------------------------------------------
        # COMPREHENSIVE TIP CARD: How to create and use variables
        # -------------------------------------------------------------
        tip_frame = QFrame()
        tip_frame.setObjectName("variableTipFrame")
        tip_frame.setStyleSheet("""
            QFrame#variableTipFrame {
                background-color: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 8px;
            }
        """)
        tip_vbox = QVBoxLayout(tip_frame)
        tip_vbox.setContentsMargins(12, 10, 12, 10)
        tip_vbox.setSpacing(5)

        tip_title_row = QHBoxLayout()
        tip_title_row.setSpacing(6)
        lbl_bulb = QLabel()
        lbl_bulb.setPixmap(get_pixmap("lightbulb", color="#16a34a", size=16))
        lbl_tip_title = QLabel("คำแนะนำและข้อกำหนดการสร้างตัวแปรใน Template ({{...}}):")
        lbl_tip_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #166534;")
        tip_title_row.addWidget(lbl_bulb)
        tip_title_row.addWidget(lbl_tip_title)
        tip_title_row.addStretch()
        tip_vbox.addLayout(tip_title_row)

        tip_text = (
            "• <b>การใส่ตัวแปร:</b> พิมพ์ชื่อตัวแปรครอบด้วยปีกกาคู่ เช่น <code>{{วันนัด}}</code>, <code>{{จำนวนเงิน}}</code>, <code>{{หมายเหตุ}}</code><br>"
            "• <b>การทำงานอัตโนมัติ:</b> เมื่อนำ Template ไปใช้ ระบบจะตรวจพบตัวแปรและ<b>สร้างช่องกรอกข้อมูลพร้อม Label ชื่อตัวแปรให้อัตโนมัติ</b>ในหน้าบันทึกรายงาน<br>"
            "• <b>กฎและคำต้องห้าม:</b> ห้ามมีช่องว่างภายในปีกกา (เช่น ใช้ <code>{{จำนวนเงิน}}</code> ห้ามใช้ <code>{{จำนวน เงิน}}</code>), "
            "ห้ามใช้อักขระ <code>&lt; &gt; &amp; &quot; '</code>, ห้ามเป็นวงเล็บว่างเปล่า <code>{{}}</code>, "
            "และห้ามใช้คำสงวนระบบ (<code>paragraphs</code>, <code>signatories</code>, <code>position</code>)"
        )
        lbl_tip_body = QLabel(tip_text)
        lbl_tip_body.setTextFormat(Qt.TextFormat.RichText)
        lbl_tip_body.setWordWrap(True)
        lbl_tip_body.setStyleSheet("font-size: 12.5px; color: #14532d; line-height: 1.45;")
        tip_vbox.addWidget(lbl_tip_body)

        right_layout.addWidget(tip_frame)

        # Form action buttons
        action_bar = QHBoxLayout()
        self.btn_delete = QPushButton("ลบ Template นี้")
        self.btn_delete.setObjectName("secondaryButton")
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #dc2626;
                border: 1.5px solid #fca5a5;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #fee2e2;
            }
            QPushButton:pressed {
                background-color: #fecaca;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """)
        self.btn_delete.setIcon(get_icon("trash", color="#dc2626", size=15))
        self.btn_delete.clicked.connect(self.delete_current)
        action_bar.addWidget(self.btn_delete)

        action_bar.addStretch()

        self.btn_save = QPushButton("บันทึกการแก้ไข")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(get_icon("save", color="#ffffff", size=15))
        self.btn_save.setStyleSheet("""
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
        self.btn_save.clicked.connect(self.save_current)
        action_bar.addWidget(self.btn_save)

        right_layout.addLayout(action_bar)
        splitter.addWidget(right_box)

        splitter.setSizes([320, 620])
        layout.addWidget(splitter)

        # Bottom Close button
        btm_bar = QHBoxLayout()
        btm_bar.addStretch()
        btn_close = QPushButton("ปิดหน้าต่าง")
        btn_close.setObjectName("secondaryButton")
        btn_close.setStyleSheet("""
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
        btn_close.clicked.connect(self.accept)
        btm_bar.addWidget(btn_close)
        layout.addLayout(btm_bar)

        self.refresh_list()

    def refresh_list(self):
        self.templates = storage_service.load_templates()
        self.filter_list()

    def filter_list(self):
        q = self.txt_filter.text().strip().lower()
        self.list_widget.clear()
        self.displayed_templates = []

        for tpl in self.templates:
            title = tpl.get("title", "")
            cat = tpl.get("category", "ทั่วไป")
            content = tpl.get("content", "")
            if q and (q not in title.lower() and q not in content.lower()):
                continue
            self.displayed_templates.append(tpl)
            item = QListWidgetItem(f"[{cat}] {title}")
            item.setData(Qt.ItemDataRole.UserRole, tpl.get("id"))
            self.list_widget.addItem(item)

        if self.displayed_templates:
            self.list_widget.setCurrentRow(0)
        else:
            self.clear_form()

    def on_order_changed(self):
        """Persist the new template order after an internal drag & drop."""
        if self.list_widget.count() == 0:
            return

        new_displayed_ids = []
        for i in range(self.list_widget.count()):
            tid = self.list_widget.item(i).data(Qt.ItemDataRole.UserRole)
            if tid is not None:
                new_displayed_ids.append(tid)

        id_to_tpl = {t.get("id"): t for t in self.templates}
        new_displayed_ids = [i for i in new_displayed_ids if i in id_to_tpl]
        if not new_displayed_ids:
            return

        displayed_set = set(new_displayed_ids)
        reordered_displayed = [id_to_tpl[i] for i in new_displayed_ids]

        # Merge: slots previously held by displayed templates take the new order;
        # non-displayed (filtered-out) templates keep their original positions.
        result = []
        di = 0
        for t in self.templates:
            if t.get("id") in displayed_set:
                result.append(reordered_displayed[di])
                di += 1
            else:
                result.append(t)
        self.templates = result
        storage_service.save_templates(self.templates)
        # Keep row -> template mapping consistent for the selection handler.
        self.displayed_templates = reordered_displayed

    def on_select_template(self, row: int):
        if 0 <= row < len(self.displayed_templates):
            tpl = self.displayed_templates[row]
            self.current_tpl_id = tpl.get("id")
            self.edt_title.setText(tpl.get("title", ""))
            self.edt_category.setText(tpl.get("category", "ส่วนตัว"))
            self.edt_content.setPlainText(tpl.get("content", ""))
            self.btn_delete.setEnabled(True)
            self.btn_save.setText("บันทึกการแก้ไข")
            self.btn_save.setIcon(get_icon("save", color="#ffffff", size=15))
        else:
            self.clear_form()

    def clear_form(self):
        self.current_tpl_id = None
        self.edt_title.clear()
        self.edt_category.setText("ส่วนตัว")
        self.edt_content.clear()
        self.btn_delete.setEnabled(False)
        self.btn_save.setText("บันทึกเป็น Template ใหม่")
        self.btn_save.setIcon(get_icon("save", color="#ffffff", size=15))

    def validate_content_variables(self):
        """Real-time validation of template variable syntax and forbidden keywords."""
        txt = self.edt_content.toPlainText()
        if '{{' not in txt and '{' not in txt:
            self.lbl_var_validation.setVisible(False)
            return

        if txt.count('{{') != txt.count('}}'):
            self.lbl_var_validation.setText("พบเครื่องหมาย {{ หรือ }} ไม่ครบคู่ กรุณาปิดวงเล็บให้สมบูรณ์")
            self.lbl_var_validation.setStyleSheet("color: #b45309; background-color: #fef3c7; border: 1px solid #fde68a;")
            self.lbl_var_validation.setVisible(True)
            return

        matches = re.findall(r'\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', txt)
        detected_custom = []
        detected_system = []
        errors = []

        for m1, m2 in matches:
            tag = (m1 or m2).strip()
            if not tag:
                errors.append("พบวงเล็บตัวแปรว่างเปล่า {{}}")
                continue
            is_valid, err = validate_template_variable(tag)
            if not is_valid:
                errors.append(err)
            elif tag in SYSTEM_RESERVED_VARIABLES:
                detected_system.append(tag)
            else:
                detected_custom.append(tag)

        if errors:
            self.lbl_var_validation.setText(f"{errors[0]}")
            self.lbl_var_validation.setStyleSheet("color: #dc2626; background-color: #fee2e2; border: 1px solid #fca5a5; font-weight: 500;")
            self.lbl_var_validation.setVisible(True)
        elif detected_custom:
            unique_custom = sorted(list(set(detected_custom)))
            vars_str = ", ".join(f"{{{{{v}}}}}" for v in unique_custom)
            self.lbl_var_validation.setText(f"ตรวจพบตัวแปรที่จะสร้างเป็นช่องกรอกข้อมูล: {vars_str}")
            self.lbl_var_validation.setStyleSheet("color: #4c1d95; background-color: #f5f3ff; border: 1px solid #ddd6fe; font-weight: 500;")
            self.lbl_var_validation.setVisible(True)
        elif detected_system:
            unique_sys = sorted(list(set(detected_system)))
            vars_str = ", ".join(f"{{{{{v}}}}}" for v in unique_sys)
            self.lbl_var_validation.setText(f"ตรวจพบตัวแปรระบบ (ดึงข้อมูลอัตโนมัติ): {vars_str}")
            self.lbl_var_validation.setStyleSheet("color: #0369a1; background-color: #f0f9ff; border: 1px solid #bae6fd;")
            self.lbl_var_validation.setVisible(True)
        else:
            self.lbl_var_validation.setVisible(False)

    def prepare_new_template(self):
        self.list_widget.clearSelection()
        self.clear_form()
        self.edt_title.setFocus()

    def save_current(self):
        title = self.edt_title.text().strip()
        category = self.edt_category.text().strip() or "ส่วนตัว"
        content = self.edt_content.toPlainText().strip()

        if not title:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อ Template")
            self.edt_title.setFocus()
            return
        if not content:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุเนื้อหาข้อความ")
            self.edt_content.setFocus()
            return

        # Check for unclosed template braces
        if content.count('{{') != content.count('}}'):
            QMessageBox.warning(
                self, "ไวยากรณ์ตัวแปรไม่สมบูรณ์",
                "พบเครื่องหมาย {{ หรือ }} ไม่ครบคู่ในเนื้อหา Template\nกรุณาตรวจสอบและปิดวงเล็บให้สมบูรณ์ก่อนบันทึก"
            )
            self.edt_content.setFocus()
            return

        # Validate all variables and check for forbidden keywords
        matches = re.findall(r'\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', content)
        for m1, m2 in matches:
            tag = (m1 or m2).strip()
            if not tag:
                QMessageBox.warning(
                    self, "ไวยากรณ์ตัวแปรไม่ถูกต้อง",
                    "พบวงเล็บตัวแปรว่างเปล่า '{{}}' ในเนื้อหา\nกรุณาระบุชื่อตัวแปรหรือลบวงเล็บออกก่อนบันทึก"
                )
                self.edt_content.setFocus()
                return
            is_valid, err_msg = validate_template_variable(tag)
            if not is_valid:
                QMessageBox.warning(
                    self, "พบคำต้องห้ามใน Template",
                    f"ไม่สามารถบันทึก Template ได้เนื่องจากพบปัญหาในตัวแปร:\n\n• {err_msg}\n\nกรุณาแก้ไขก่อนบันทึก"
                )
                self.edt_content.setFocus()
                return

        if self.current_tpl_id:
            storage_service.update_template(self.current_tpl_id, title, content, category)
            QMessageBox.information(self, "สำเร็จ", "บันทึกการแก้ไข Template เรียบร้อยแล้ว")
        else:
            new_tpl = storage_service.add_template(title, content, category)
            self.current_tpl_id = new_tpl.get("id")
            QMessageBox.information(self, "สำเร็จ", "เพิ่ม Template ใหม่เรียบร้อยแล้ว")

        self.refresh_list()

    def delete_current(self):
        if not self.current_tpl_id:
            return
        reply = QMessageBox.question(
            self, "ยืนยันการลบ",
            f"คุณต้องการลบ Template '{self.edt_title.text()}' ใช่หรือไม่?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            storage_service.delete_template(self.current_tpl_id)
            QMessageBox.information(self, "สำเร็จ", "ลบ Template เรียบร้อยแล้ว")
            self.refresh_list()
