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
    QMessageBox, QSplitter, QInputDialog, QMenu, QScrollArea
)
from PySide6.QtCore import Qt
from services import storage_service
from services.docx_service import validate_template_variable, SYSTEM_RESERVED_VARIABLES
from services.template_variable_service import parse_variable_tag
from services.icon_service import get_icon, get_pixmap, get_app_logo_icon
from ui.components.draggable_list import DraggableListWidget
from ui.components.template_chip_highlighter import TemplateChipHighlighter
from ui.dialogs.variable_define_dialog import VariableDefineDialog
from ui.components.template_chip_menu import (
    show_date_chip_menu,
    show_time_chip_menu,
    show_money_chip_menu,
    show_select_chip_menu,
    show_text_chip_menu,
    prompt_custom_variable_define,
)


class TemplateManagerDialog(QDialog):
    """Full management dialog to Add, Edit, Delete paragraph templates."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("จัดการ Template ข้อความกระบวนพิจารณา - CODS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(1020, 720)
        self.setMinimumSize(940, 640)
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
        lbl_sub = QLabel("เพิ่ม แก้ไข หรือลบข้อความสำเร็จรูป พร้อมกำหนดตัวแปร [ชื่อตัวแปร] เพื่อให้ระบบสร้างช่องกรอกอัตโนมัติ")
        lbl_sub.setStyleSheet("font-size: 13px; color: #64748b;")
        v_title.addWidget(lbl_title)
        v_title.addWidget(lbl_sub)
        top_bar.addLayout(v_title)
        top_bar.addStretch()

        # Action buttons on top bar
        btn_word_recovery = QPushButton("กู้คืนแม่แบบ Word...")
        btn_word_recovery.setObjectName("secondaryButtonSmall")
        btn_word_recovery.setIcon(get_icon("file-text", color="#4c1d95", size=14))
        btn_word_recovery.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #d8b4fe;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
            }
        """)
        btn_word_recovery.clicked.connect(self.open_word_template_recovery)
        top_bar.addWidget(btn_word_recovery)

        btn_reset_defaults = QPushButton("กู้คืน Template เริ่มต้น")
        btn_reset_defaults.setObjectName("secondaryButtonSmall")
        btn_reset_defaults.setIcon(get_icon("rotate-ccw", color="#475569", size=14))
        btn_reset_defaults.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
            }
        """)
        btn_reset_defaults.clicked.connect(self.handle_restore_default_paragraphs)
        top_bar.addWidget(btn_reset_defaults)

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
        right_layout.setContentsMargins(16, 12, 16, 12)
        right_layout.setSpacing(8)

        lbl_edit_title = QLabel("รายละเอียด Template")
        lbl_edit_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0f172a;")
        right_layout.addWidget(lbl_edit_title)

        form_meta = QHBoxLayout()
        form_meta.setSpacing(10)
        v_name = QVBoxLayout()
        v_name.setSpacing(3)
        lbl_t = QLabel("ชื่อ Template:")
        lbl_t.setStyleSheet("font-size: 12.5px; font-weight: 600; color: #334155;")
        self.edt_title = QLineEdit()
        self.edt_title.setPlaceholderText("ระบุชื่อหัวข้อ Template เช่น ไกล่เกลี่ยสำเร็จ, เลื่อนนัดพร้อม")
        v_name.addWidget(lbl_t)
        v_name.addWidget(self.edt_title)
        form_meta.addLayout(v_name, 2)

        v_cat = QVBoxLayout()
        v_cat.setSpacing(3)
        lbl_c = QLabel("หมวดหมู่:")
        lbl_c.setStyleSheet("font-size: 12.5px; font-weight: 600; color: #334155;")
        self.edt_category = QLineEdit()
        self.edt_category.setPlaceholderText("เช่น ทั่วไป, นัดพร้อม, คำพิพากษา")
        v_cat.addWidget(lbl_c)
        v_cat.addWidget(self.edt_category)
        form_meta.addLayout(v_cat, 1)
        right_layout.addLayout(form_meta)

        # Label Row
        lbl_body = QLabel("เนื้อหาข้อความกระบวนพิจารณา:")
        lbl_body.setStyleSheet("font-size: 12.5px; font-weight: 600; color: #334155;")
        right_layout.addWidget(lbl_body)

        # Quick Chip Toolbar Row
        h_chip_bar = QHBoxLayout()
        h_chip_bar.setSpacing(6)

        lbl_chip_hint = QLabel("แทรกชิปตัวแปร:")
        lbl_chip_hint.setStyleSheet("font-size: 11.5px; color: #6b21a8; font-weight: 600;")
        h_chip_bar.addWidget(lbl_chip_hint)

        chip_btn_style = """
            QPushButton {
                background-color: #f5f3ff;
                color: #581c87;
                border: 1px solid #d8b4fe;
                border-radius: 4px;
                padding: 2.5px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ede9fe;
                border-color: #a855f7;
            }
            QPushButton:pressed {
                background-color: #ddd6fe;
            }
        """

        btn_chip_date = QPushButton("📅 วันที่ ▾")
        btn_chip_date.setStyleSheet(chip_btn_style)
        btn_chip_date.setToolTip("เลือกแทรกตัวแปรประเภทวันที่ (แบบเต็ม, แบบย่อ, ตัวเลข, ทางการศาล)")
        btn_chip_date.clicked.connect(lambda: self.show_date_chip_menu(btn_chip_date))
        h_chip_bar.addWidget(btn_chip_date)

        btn_chip_time = QPushButton("⏰ เวลา ▾")
        btn_chip_time.setStyleSheet(chip_btn_style)
        btn_chip_time.setToolTip("เลือกแทรกตัวแปรประเภทเวลา (ทางการศาล หรือเวลาทั่วไป)")
        btn_chip_time.clicked.connect(lambda: self.show_time_chip_menu(btn_chip_time))
        h_chip_bar.addWidget(btn_chip_time)

        btn_chip_money = QPushButton("🔢 จำนวนเงิน ▾")
        btn_chip_money.setStyleSheet(chip_btn_style)
        btn_chip_money.setToolTip("เลือกแทรกตัวแปรตัวเลขหรือจำนวนเงิน")
        btn_chip_money.clicked.connect(lambda: self.show_money_chip_menu(btn_chip_money))
        h_chip_bar.addWidget(btn_chip_money)

        btn_chip_select = QPushButton("📋 ตัวเลือก ▾")
        btn_chip_select.setStyleSheet(chip_btn_style)
        btn_chip_select.setToolTip("เลือกแทรกตัวแปรแบบรายการตัวเลือก (Dropdown)")
        btn_chip_select.clicked.connect(lambda: self.show_select_chip_menu(btn_chip_select))
        h_chip_bar.addWidget(btn_chip_select)

        btn_chip_text = QPushButton("✏️ ข้อความ ▾")
        btn_chip_text.setStyleSheet(chip_btn_style)
        btn_chip_text.setToolTip("แทรกตัวแปรข้อความทั่วไป เช่น ชื่อพยาน, หมายเหตุ")
        btn_chip_text.clicked.connect(lambda: self.show_text_chip_menu(btn_chip_text))
        h_chip_bar.addWidget(btn_chip_text)

        btn_chip_custom = QPushButton("+ กำหนดประเภทเอง...")
        btn_chip_custom.setStyleSheet("""
            QPushButton {
                background-color: #ede9fe;
                color: #4c1d95;
                border: 1px solid #c4b5fd;
                border-radius: 4px;
                padding: 2.5px 9px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #ddd6fe;
                border-color: #8b5cf6;
            }
        """)
        btn_chip_custom.setToolTip("เปิดหน้าต่างเลือกประเภทตัวแปร (วันที่, เวลา, ตัวเลข, ตัวเลือก, ข้อความ) และกำหนดชื่อได้อย่างอิสระ")
        btn_chip_custom.clicked.connect(lambda: self.prompt_custom_chip_to_editor())
        h_chip_bar.addWidget(btn_chip_custom)
        h_chip_bar.addStretch()

        right_layout.addLayout(h_chip_bar)

        self.edt_content = QTextEdit()
        self.edt_content.setPlaceholderText("พิมพ์เนื้อหาข้อความกระบวนพิจารณา... ท่านสามารถคลิกปุ่มชิปด้านบนเพื่อแทรกตัวแปรได้อย่างสะดวกรวดเร็ว")
        self.edt_content.setMinimumHeight(110)
        
        # Install Visual Chip Syntax Highlighter & Interactive Key Filter
        self.highlighter = TemplateChipHighlighter(self.edt_content)
        right_layout.addWidget(self.edt_content, 1)

        # Real-time Variable Validation Indicator
        self.lbl_var_validation = QLabel()
        self.lbl_var_validation.setWordWrap(True)
        self.lbl_var_validation.setStyleSheet("font-size: 12px; padding: 4px 8px; border-radius: 4px;")
        self.lbl_var_validation.setVisible(False)
        right_layout.addWidget(self.lbl_var_validation)
        self.edt_content.textChanged.connect(self.validate_content_variables)

        # -------------------------------------------------------------
        # COMPACT TIP BANNER: How to create and use variables
        # -------------------------------------------------------------
        tip_frame = QFrame()
        tip_frame.setObjectName("variableTipFrame")
        tip_frame.setStyleSheet("""
            QFrame#variableTipFrame {
                background-color: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 6px;
            }
        """)
        tip_vbox = QVBoxLayout(tip_frame)
        tip_vbox.setContentsMargins(10, 6, 10, 6)
        tip_vbox.setSpacing(2)

        tip_title_row = QHBoxLayout()
        tip_title_row.setSpacing(5)
        lbl_bulb = QLabel()
        lbl_bulb.setPixmap(get_pixmap("lightbulb", color="#16a34a", size=13))
        lbl_tip_title = QLabel("คำแนะนำชิปตัวแปร:")
        lbl_tip_title.setStyleSheet("font-size: 11.5px; font-weight: 700; color: #166534;")
        tip_title_row.addWidget(lbl_bulb)
        tip_title_row.addWidget(lbl_tip_title)

        tip_text_line1 = QLabel("คลิกปุ่มด้านบน หรือพิมพ์ <code>[ชื่อ:ประเภท]</code> เช่น วันที่, เวลา, Dropdown — ระบบสร้างช่องกรอกตามประเภทให้อัตโนมัติ")
        tip_text_line1.setTextFormat(Qt.TextFormat.RichText)
        tip_text_line1.setStyleSheet("font-size: 11px; color: #14532d;")
        tip_title_row.addWidget(tip_text_line1)
        tip_title_row.addStretch()
        tip_vbox.addLayout(tip_title_row)

        tip_text_line2 = QLabel("กด <b>Backspace</b> หลังชิปเพื่อเข้าไปแก้ชื่อด้านใน | หากลบตัวอักษรในชิปจนหมด ชิปจะหายไปทันที")
        tip_text_line2.setTextFormat(Qt.TextFormat.RichText)
        tip_text_line2.setStyleSheet("font-size: 11px; color: #15803d; padding-left: 18px;")
        tip_vbox.addWidget(tip_text_line2)

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
                padding: 6px 14px;
                font-size: 12.5px;
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
        self.btn_delete.setIcon(get_icon("trash", color="#dc2626", size=14))
        self.btn_delete.clicked.connect(self.delete_current)
        action_bar.addWidget(self.btn_delete)

        action_bar.addStretch()

        self.btn_save = QPushButton("บันทึกการแก้ไข")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(get_icon("save", color="#ffffff", size=14))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                padding: 7px 18px;
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

        splitter.setSizes([320, 680])
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
            if not self.templates:
                empty_item = QListWidgetItem("ยังไม่มี Template ในระบบ\nพิมพ์ข้อมูลฝั่งขวาแล้วกด 'บันทึกเป็น Template ใหม่'")
                empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
                empty_item.setForeground(Qt.GlobalColor.darkGray)
                self.list_widget.addItem(empty_item)

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
            raw_cnt = tpl.get("content", "")
            cleaned_cnt = re.sub(r'\{\{\s*([^}]+?)\s*\}\}', r'[\1]', raw_cnt)
            cleaned_cnt = re.sub(r'\{([^{}\n]+?)\}', r'[\1]', cleaned_cnt)
            cleaned_cnt = re.sub(r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]]+?)\s*\]', r'[\1]', cleaned_cnt)
            self.edt_content.setPlainText(cleaned_cnt)
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

    def insert_chip_to_editor(self, var_name: str):
        """Insert variable chip text into edt_content at current cursor position without raw {{}}."""
        chip_text = f"[{var_name}]"
        cursor = self.edt_content.textCursor()
        cursor.insertText(chip_text)
        self.edt_content.setTextCursor(cursor)
        self.edt_content.setFocus()

    def show_date_chip_menu(self, btn: QPushButton):
        """Show dropdown menu offering all date format choices for template insertion."""
        show_date_chip_menu(btn, self, self.insert_chip_to_editor)

    def show_time_chip_menu(self, btn: QPushButton):
        """Show dropdown menu offering time formats for template insertion."""
        show_time_chip_menu(btn, self, self.insert_chip_to_editor)

    def show_money_chip_menu(self, btn: QPushButton):
        """Show dropdown menu offering number and currency variables."""
        show_money_chip_menu(btn, self, self.insert_chip_to_editor)

    def show_select_chip_menu(self, btn: QPushButton):
        """Show dropdown menu offering dropdown/select variables."""
        show_select_chip_menu(btn, self, self.insert_chip_to_editor)

    def show_text_chip_menu(self, btn: QPushButton):
        """Show dropdown menu offering common text variables."""
        show_text_chip_menu(btn, self, self.insert_chip_to_editor)

    def prompt_custom_chip_to_editor(self, initial_type: str = "date"):
        """Open VariableDefineDialog allowing user to choose input type, date format, and name."""
        prompt_custom_variable_define(self, self.insert_chip_to_editor, initial_type)

    def validate_content_variables(self):
        """Real-time validation of template variable syntax and forbidden keywords."""
        txt = self.edt_content.toPlainText()
        if '[' not in txt and '{' not in txt:
            self.lbl_var_validation.setVisible(False)
            return

        matches = re.findall(r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]]+?)\s*\]|\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', txt)
        detected_custom = []
        detected_system = []
        errors = []

        for m1, m2, m3 in matches:
            tag = (m1 or m2 or m3).strip()
            tag = re.sub(r'^[\U0001f3f7\ufe0f\s]+', '', tag).strip()
            if not tag:
                errors.append("พบวงเล็บชิปตัวแปรว่างเปล่า")
                continue
            is_valid, err = validate_template_variable(tag)
            if not is_valid:
                errors.append(err)
            elif tag in SYSTEM_RESERVED_VARIABLES or tag.split(':')[0].strip() in SYSTEM_RESERVED_VARIABLES:
                detected_system.append(tag)
            else:
                detected_custom.append(tag)

        if errors:
            self.lbl_var_validation.setText(f"{errors[0]}")
            self.lbl_var_validation.setStyleSheet("color: #dc2626; background-color: #fee2e2; border: 1px solid #fca5a5; font-weight: 500;")
            self.lbl_var_validation.setVisible(True)
        elif detected_custom:
            unique_custom = sorted(list(set(detected_custom)))
            chips_labels = []
            for v in unique_custom:
                meta = parse_variable_tag(v)
                chips_labels.append(f"[{meta['name']}]")
            chips_str = "   ".join(chips_labels)
            self.lbl_var_validation.setText(f"ตรวจพบชิปตัวแปรที่จะสร้างเป็นกล่องกรอกข้อมูล: {chips_str}")
            self.lbl_var_validation.setStyleSheet("color: #4c1d95; background-color: #f5f3ff; border: 1px solid #ddd6fe; font-weight: 500;")
            self.lbl_var_validation.setVisible(True)
        elif detected_system:
            unique_sys = sorted(list(set(detected_system)))
            chips_str = "   ".join(f"[{v}]" for v in unique_sys)
            self.lbl_var_validation.setText(f"ตรวจพบตัวแปรระบบ (ดึงข้อมูลอัตโนมัติ): {chips_str}")
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

        # Check for unclosed template braces or brackets
        if content.count('{{') != content.count('}}') or content.count('[') != content.count(']'):
            QMessageBox.warning(
                self, "ไวยากรณ์ตัวแปรไม่สมบูรณ์",
                "พบเครื่องหมายวงเล็บตัวแปรไม่ครบคู่ในเนื้อหา Template\nกรุณาตรวจสอบและปิดวงเล็บให้สมบูรณ์ก่อนบันทึก"
            )
            self.edt_content.setFocus()
            return

        # Validate all variables and check for forbidden keywords
        matches = re.findall(r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]]+?)\s*\]|\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', content)
        for m1, m2, m3 in matches:
            tag = (m1 or m2 or m3).strip()
            tag = re.sub(r'^[\U0001f3f7\ufe0f\s]+', '', tag).strip()
            if not tag:
                QMessageBox.warning(
                    self, "ไวยากรณ์ตัวแปรไม่ถูกต้อง",
                    "พบวงเล็บตัวแปรว่างเปล่าในเนื้อหา\nกรุณาระบุชื่อตัวแปรหรือลบวงเล็บออกก่อนบันทึก"
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

    def open_word_template_recovery(self):
        from ui.dialogs.template_recovery_dialog import TemplateRecoveryDialog
        dlg = TemplateRecoveryDialog(self)
        dlg.exec()

    def handle_restore_default_paragraphs(self):
        reply = QMessageBox.question(
            self, "ยืนยันการกู้คืน Template เริ่มต้น",
            "ท่านต้องการกู้คืน Template ข้อความกระบวนพิจารณาเริ่มต้นของระบบใช่หรือไม่?\n\n"
            "ระบบจะนำแบบข้อความสำเร็จรูปมาตรฐาน (7 รายการ) กลับคืนสู่ระบบ",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        from services.template_recovery_service import restore_default_paragraph_templates
        ok, msg = restore_default_paragraph_templates()
        if ok:
            QMessageBox.information(self, "สำเร็จ", msg)
            self.refresh_list()
        else:
            QMessageBox.warning(self, "แจ้งเตือน", msg)

