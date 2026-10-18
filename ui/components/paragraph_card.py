"""
Paragraph Card Component
Card representing one discrete paragraph with text box,
Drag & Drop reordering, template insertion, and template saving.
"""
import re
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QMessageBox, QMenu, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QEvent, QMimeData, QTimer
from PySide6.QtGui import QDrag
from services.icon_service import get_icon, get_pixmap
from ui.dialogs.template_select_dialog import TemplateSelectDialog
from ui.components.draggable_list import DraggableListWidget
from ui.components.template_chip_highlighter import TemplateChipHighlighter
from ui.components.variable_chip_widget import VariableChipComponent
from services.template_variable_service import get_variable_replace_pattern, parse_variable_tag, format_number_comma
from ui.dialogs.variable_define_dialog import VariableDefineDialog
from ui.components.template_chip_menu import show_combined_chip_menu, prompt_custom_variable_define


class ParagraphCard(QFrame):
    """
    Card representing one discrete paragraph with text box,
    Drag & Drop reordering, template insertion, and template saving.
    """
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    delete_requested = Signal(object)
    reorder_requested = Signal(int, int)  # (source_1based_index, target_1based_index)
    text_changed = Signal()
    chip_value_changed = Signal(str, str)  # (var_name, new_val)

    def __init__(self, index: int = 1, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("paragraphCard")
        self.setAcceptDrops(True)
        self.drag_start_pos = None
        self.init_ui(text)

    def init_ui(self, initial_text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(10)

        # Header Row
        header_bar = QHBoxLayout()
        header_bar.setSpacing(8)

        # Drag grip handle
        self.drag_grip = QFrame()
        self.drag_grip.setObjectName("dragGripHandle")
        self.drag_grip.setToolTip("คลิกค้างแล้วลากเพื่อสลับลำดับย่อหน้านี้ (Drag & Drop)")
        self.drag_grip.setCursor(Qt.CursorShape.OpenHandCursor)
        grip_l = QHBoxLayout(self.drag_grip)
        grip_l.setContentsMargins(6, 4, 8, 4)
        grip_l.setSpacing(6)
        lbl_grip_icon = QLabel()
        lbl_grip_icon.setPixmap(get_pixmap("grip-vertical", color="#64748b", size=16))
        lbl_grip_txt = QLabel("ลากสลับตำแหน่ง")
        lbl_grip_txt.setStyleSheet("color: #475569; font-weight: 500; font-size: 13px;")
        grip_l.addWidget(lbl_grip_icon)
        grip_l.addWidget(lbl_grip_txt)
        self.drag_grip.installEventFilter(self)
        header_bar.addWidget(self.drag_grip)

        self.lbl_badge = QLabel(f"ย่อหน้าที่ {self.index}")
        self.lbl_badge.setObjectName("paragraphBadge")
        self.lbl_badge.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #4c1d95; "
            "background-color: #ede9fe; padding: 4px 10px; border-radius: 4px;"
        )
        header_bar.addWidget(self.lbl_badge)

        header_bar.addStretch()

        btn_mini_style = """
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #ddd6fe;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f5f3ff;
                border-color: #c4b5fd;
                color: #3b0764;
            }
            QPushButton:pressed {
                background-color: #ede9fe;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """

        self.btn_insert_chip = QPushButton("+ แทรกตัวแปร (Chip)")
        self.btn_insert_chip.setObjectName("cardMiniButton")
        self.btn_insert_chip.setStyleSheet("""
            QPushButton {
                background-color: #f5f3ff;
                color: #4c1d95;
                border: 1.5px solid #c4b5fd;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ede9fe;
                border-color: #8b5cf6;
                color: #3b0764;
            }
            QPushButton:pressed {
                background-color: #ddd6fe;
            }
        """)
        self.btn_insert_chip.setIcon(get_icon("tag", color="#4c1d95", size=14))
        self.btn_insert_chip.setToolTip("แทรกชิปตัวแปร {{...}} ลงในข้อความ เพื่อให้กรอกข้อมูลได้สะดวก")
        self.btn_insert_chip.clicked.connect(self.show_chip_menu)
        header_bar.addWidget(self.btn_insert_chip)

        self.btn_insert_tpl = QPushButton("แทรก Template")
        self.btn_insert_tpl.setObjectName("cardMiniButton")
        self.btn_insert_tpl.setStyleSheet(btn_mini_style)
        self.btn_insert_tpl.setIcon(get_icon("clipboard-list", color="#4c1d95", size=15))
        self.btn_insert_tpl.setToolTip("เลือกข้อความสำเร็จรูปจาก Template มาใส่ในย่อหน้านี้")
        self.btn_insert_tpl.clicked.connect(self.handle_insert_template)
        header_bar.addWidget(self.btn_insert_tpl)

        self.btn_save_tpl = QPushButton("บันทึกเป็น Template")
        self.btn_save_tpl.setObjectName("cardMiniButton")
        self.btn_save_tpl.setStyleSheet(btn_mini_style)
        self.btn_save_tpl.setIcon(get_icon("save", color="#4c1d95", size=15))
        self.btn_save_tpl.setToolTip("บันทึกข้อความในย่อหน้านี้เป็น Template ส่วนตัว")
        self.btn_save_tpl.clicked.connect(self.handle_save_template)
        header_bar.addWidget(self.btn_save_tpl)

        self.btn_up = QPushButton("เลื่อนขึ้น")
        self.btn_up.setObjectName("cardMiniButton")
        self.btn_up.setStyleSheet(btn_mini_style)
        self.btn_up.setIcon(get_icon("chevron-up", color="#4c1d95", size=15))
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self))
        header_bar.addWidget(self.btn_up)

        self.btn_down = QPushButton("เลื่อนลง")
        self.btn_down.setObjectName("cardMiniButton")
        self.btn_down.setStyleSheet(btn_mini_style)
        self.btn_down.setIcon(get_icon("chevron-down", color="#4c1d95", size=15))
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self))
        header_bar.addWidget(self.btn_down)

        self.btn_del = QPushButton("ลบ")
        self.btn_del.setObjectName("cardMiniButtonDanger")
        self.btn_del.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #dc2626;
                border: 1.5px solid #fca5a5;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                color: #991b1b;
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
        self.btn_del.setIcon(get_icon("trash", color="#dc2626", size=15))
        self.btn_del.setToolTip("ลบย่อหน้านี้")
        self.btn_del.clicked.connect(self.handle_delete)
        header_bar.addWidget(self.btn_del)

        layout.addLayout(header_bar)

        # Paragraph Text Editor
        self.txt_editor = QTextEdit()
        self.txt_editor.setPlaceholderText(f"ระบุข้อความกระบวนพิจารณาสำหรับย่อหน้าที่ {self.index}... (กดปุ่ม '+ แทรกตัวแปร' เพื่อแทรกชิปตัวแปรอัตโนมัติ)")
        cleaned_init = re.sub(r'\{\{\s*([^}]+?)\s*\}\}', r'[\1]', initial_text)
        cleaned_init = re.sub(r'\{([^{}\n]+?)\}', r'[\1]', cleaned_init)
        cleaned_init = re.sub(r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]]+?)\s*\]', r'[\1]', cleaned_init)
        self.txt_editor.setPlainText(cleaned_init)
        self.txt_editor.textChanged.connect(self._on_internal_text_changed)
        
        # Install Visual Chip Syntax Highlighter & Interactive Key Filter
        self.highlighter = TemplateChipHighlighter(self.txt_editor)
        layout.addWidget(self.txt_editor)

        # -------------------------------------------------------------
        # Interactive Variable Chips & Quick Fill Panel
        # -------------------------------------------------------------
        self.var_panel = QFrame()
        self.var_panel.setObjectName("paragraphVarChipsPanel")
        self.var_panel.setStyleSheet("""
            QFrame#paragraphVarChipsPanel {
                background-color: #faf5ff;
                border: 1.5px solid #ddd6fe;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.var_panel_layout = QVBoxLayout(self.var_panel)
        self.var_panel_layout.setContentsMargins(10, 8, 10, 8)
        self.var_panel_layout.setSpacing(8)

        # Header for variables panel
        var_head = QHBoxLayout()
        var_head.setSpacing(6)
        lbl_chip_icon = QLabel()
        lbl_chip_icon.setPixmap(get_pixmap("tag", color="#6b21a8", size=15))
        lbl_var_title = QLabel("ตัวแปรใน Template นี้ (กรอกข้อมูลเพื่อแทนที่คำอัตโนมัติ):")
        lbl_var_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #581c87;")
        var_head.addWidget(lbl_chip_icon)
        var_head.addWidget(lbl_var_title)
        var_head.addStretch()

        self.btn_apply_chips = QPushButton("แทนที่ทั้งหมดในข้อความ")
        self.btn_apply_chips.setIcon(get_icon("check", color="#ffffff", size=13))
        self.btn_apply_chips.setStyleSheet("""
            QPushButton {
                background-color: #6b21a8;
                color: #ffffff;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover { background-color: #7e22ce; }
            QPushButton:pressed { background-color: #581c87; }
        """)
        self.btn_apply_chips.setToolTip("นำค่าที่กรอกในกล่องตัวแปรทั้งหมดไปแทนที่ในย่อหน้านี้ทันที")
        self.btn_apply_chips.clicked.connect(self.apply_variable_values)
        var_head.addWidget(self.btn_apply_chips)
        self.var_panel_layout.addLayout(var_head)

        # Container for variable chip component widgets
        self.chips_container = QVBoxLayout()
        self.chips_container.setSpacing(6)
        self.var_panel_layout.addLayout(self.chips_container)

        self.chip_components: dict[str, VariableChipComponent] = {}
        self.var_inputs: dict[str, QLineEdit] = {}
        layout.addWidget(self.var_panel)
        self._update_vars_badge()

    def show_chip_menu(self):
        """Display quick menu to pick or create template variable chips with formats."""
        show_combined_chip_menu(self.btn_insert_chip, self, self.insert_variable_chip)

    def prompt_custom_chip(self, initial_type: str = "date"):
        """Open rich VariableDefineDialog to configure variable with input type and date format."""
        prompt_custom_variable_define(self, self.insert_variable_chip, initial_type)

    def insert_variable_chip(self, var_name: str):
        """Insert [var_name] into txt_editor at current cursor position without raw {{}}."""
        chip_text = f"[{var_name}]"
        cursor = self.txt_editor.textCursor()
        cursor.insertText(chip_text)
        self.txt_editor.setTextCursor(cursor)
        self.txt_editor.setFocus()

    def apply_single_chip_value(self, var_name: str, value: str):
        """Replace a single variable in txt_editor immediately using type-aware regex."""
        val = value.strip()
        if not val:
            return
        meta = parse_variable_tag(var_name)
        if meta.get('type') == 'number' or any(k in var_name for k in ('เงิน', 'บาท', 'จำนวน', 'ยอด', 'ราคา', 'ทุนทรัพย์', 'ดอกเบี้ย')):
            val = format_number_comma(val)
        current_text = self.get_text()
        base_name = meta['name']
        pattern = get_variable_replace_pattern(base_name)
        if pattern.search(current_text):
            current_text = pattern.sub(val, current_text)
            self.set_text(current_text)
            self._update_vars_badge()
            self.text_changed.emit()

    def apply_variable_values(self):
        """Replace all variables with values typed in the variable chip widgets immediately."""
        current_text = self.get_text()
        replaced = False
        for var_name, comp in self.chip_components.items():
            val = comp.get_value()
            if val:
                meta = parse_variable_tag(var_name)
                if meta.get('type') == 'number' or any(k in var_name for k in ('เงิน', 'บาท', 'จำนวน', 'ยอด', 'ราคา', 'ทุนทรัพย์', 'ดอกเบี้ย')):
                    val = format_number_comma(val)
                base_name = getattr(comp, 'base_name', meta['name'])
                pattern = get_variable_replace_pattern(base_name)
                if pattern.search(current_text):
                    current_text = pattern.sub(val, current_text)
                    replaced = True
        
        if replaced:
            self.set_text(current_text)
            self._update_vars_badge()
            self.text_changed.emit()
            if hasattr(self, 'btn_apply_chips'):
                b = self.btn_apply_chips
                b.setText("แทนที่เรียบร้อย")
                b.setIcon(get_icon("check", color="#ffffff", size=13))
                b.setStyleSheet("background-color: #16a34a; color: #ffffff; border-radius: 4px; padding: 4px 12px; font-size: 12px; font-weight: 600; border: none;")
                QTimer.singleShot(1500, lambda: (
                    b.setText("แทนที่ทั้งหมดในข้อความ"),
                    b.setIcon(get_icon("check", color="#ffffff", size=13)),
                    b.setStyleSheet("background-color: #6b21a8; color: #ffffff; border-radius: 4px; padding: 4px 12px; font-size: 12px; font-weight: 600; border: none;")
                ))

    def _on_internal_text_changed(self):
        self._update_vars_badge()
        self.text_changed.emit()

    def _update_vars_badge(self):
        txt = self.get_text()
        matches = re.findall(r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]]+?)\s*\]|\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', txt)
        vars_found = []
        for m1, m2, m3 in matches:
            t = (m1 or m2 or m3).strip()
            t = re.sub(r'^[\U0001f3f7\ufe0f\s]+', '', t).strip()
            if t and not t.startswith(('#', '/')):
                vars_found.append(t)

        unique_vars = sorted(list(set(vars_found)))
        
        # If no variables, hide the panel
        if not unique_vars:
            self.var_panel.setVisible(False)
            self.chip_components.clear()
            self.var_inputs.clear()
            return

        # Keep existing typed values
        saved_values = {}
        for k, comp in self.chip_components.items():
            saved_values[k] = comp.get_value()
        for k, edt in self.var_inputs.items():
            if k not in saved_values:
                saved_values[k] = edt.text()

        # Clear layout
        while self.chips_container.count():
            item = self.chips_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        self.chip_components.clear()
        self.var_inputs.clear()

        # Check sibling cards or parent page if saved_values doesn't have it
        p = self.parent()
        for v in unique_vars:
            base_v = parse_variable_tag(v)['name']
            val = saved_values.get(v, "") or saved_values.get(base_v, "")
            if not val and p and hasattr(p, 'paragraph_cards'):
                for other_card in p.paragraph_cards:
                    if other_card is not self and hasattr(other_card, 'chip_components'):
                        for c_key, c_comp in other_card.chip_components.items():
                            c_base = parse_variable_tag(c_key)['name']
                            if c_key == v or c_base == base_v:
                                cand = c_comp.get_value()
                                if cand:
                                    val = cand
                                    break
            if not val and p and hasattr(p, 'dynamic_inputs'):
                target_inp = p.dynamic_inputs.get(v) or p.dynamic_inputs.get(base_v)
                if target_inp:
                    val = target_inp.text() if hasattr(target_inp, 'text') else getattr(target_inp, 'get_value', lambda: '')()

            chip_comp = VariableChipComponent(v, val, parent=self.var_panel)
            chip_comp.apply_requested.connect(self.apply_single_chip_value)
            chip_comp.value_changed.connect(lambda var_n, val: self.chip_value_changed.emit(var_n, val))
            self.chip_components[v] = chip_comp
            if base_v and base_v not in self.chip_components:
                self.chip_components[base_v] = chip_comp
            self.var_inputs[v] = chip_comp.txt_value
            self.chips_container.addWidget(chip_comp)

        self.var_panel.setVisible(True)


    def eventFilter(self, source, event):
        if source == self.drag_grip:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.drag_start_pos = event.pos()
                self.drag_grip.setCursor(Qt.CursorShape.ClosedHandCursor)
            elif event.type() == QEvent.Type.MouseMove and event.buttons() == Qt.MouseButton.LeftButton:
                if self.drag_start_pos and (event.pos() - self.drag_start_pos).manhattanLength() > 4:
                    drag = QDrag(self)
                    mime_data = QMimeData()
                    mime_data.setData("application/x-cods-paragraph", str(self.index).encode('utf-8'))
                    mime_data.setData("application/x-jads-paragraph", str(self.index).encode('utf-8'))
                    drag.setMimeData(mime_data)
                    drag.exec(Qt.DropAction.MoveAction)
                    self.drag_grip.setCursor(Qt.CursorShape.OpenHandCursor)
                    self.drag_start_pos = None
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.drag_grip.setCursor(Qt.CursorShape.OpenHandCursor)
                self.drag_start_pos = None
        return super().eventFilter(source, event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-cods-paragraph") or event.mimeData().hasFormat("application/x-jads-paragraph"):
            event.acceptProposedAction()
            self.setProperty("dropTarget", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("dropTarget", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event):
        self.setProperty("dropTarget", False)
        self.style().unpolish(self)
        self.style().polish(self)
        mime = event.mimeData()
        if mime.hasFormat("application/x-cods-paragraph") or mime.hasFormat("application/x-jads-paragraph"):
            try:
                tag = "application/x-cods-paragraph" if mime.hasFormat("application/x-cods-paragraph") else "application/x-jads-paragraph"
                src_str = mime.data(tag).data().decode('utf-8')
                src_idx = int(src_str)
                target_idx = self.index
                if src_idx != target_idx:
                    self.reorder_requested.emit(src_idx, target_idx)
                event.acceptProposedAction()
            except Exception:
                pass

    def set_index(self, index: int, is_first: bool = False, is_last: bool = False):
        self.index = index
        self.lbl_badge.setText(f"ย่อหน้าที่ {self.index}")
        self.txt_editor.setPlaceholderText(f"ระบุข้อความกระบวนพิจารณาสำหรับย่อหน้าที่ {self.index}...")
        self.btn_up.setEnabled(not is_first)
        self.btn_down.setEnabled(not is_last)

    @property
    def txt_content(self):
        """Backward compatibility alias for txt_editor."""
        return self.txt_editor

    def get_text(self) -> str:
        return self.txt_editor.toPlainText().strip()

    def set_text(self, text: str):
        # Clean any legacy {{var}} or [var] to standard chip syntax [var]
        cleaned = re.sub(r'\{\{\s*([^}]+?)\s*\}\}', r'[\1]', text)
        cleaned = re.sub(r'\{([^{}\n]+?)\}', r'[\1]', cleaned)
        cleaned = re.sub(r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]]+?)\s*\]', r'[\1]', cleaned)
        self.txt_editor.setPlainText(cleaned)

    def handle_insert_template(self):
        dlg = TemplateSelectDialog(self)
        if dlg.exec() and dlg.selected_content:
            existing = self.get_text()
            if existing:
                reply = QMessageBox.question(
                    self, "ยืนยันการแทรก Template",
                    "ย่อหน้านี้มีข้อความอยู่แล้ว คุณต้องการแทนที่ข้อความเดิม (Yes) หรือต่อท้ายข้อความเดิม (No)?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.set_text(dlg.selected_content)
                elif reply == QMessageBox.StandardButton.No:
                    self.set_text(existing + "\n" + dlg.selected_content)
            else:
                self.set_text(dlg.selected_content)

    def handle_save_template(self):
        text = self.get_text()
        if not text:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาพิมพ์ข้อความในย่อหน้านี้ก่อนทำการบันทึกเป็น Template")
            return
        from ui.dialogs.save_template_modal import SaveTemplateModal
        dlg = SaveTemplateModal(text, self)
        dlg.exec()

    def handle_delete(self):
        text = self.get_text()
        if text:
            reply = QMessageBox.question(
                self, "ยืนยันการลบย่อหน้า",
                f"คุณต้องการลบย่อหน้าที่ {self.index} หรือไม่?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self.delete_requested.emit(self)
