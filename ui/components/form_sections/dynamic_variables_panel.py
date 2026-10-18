"""
Dynamic Template Variables Panel Component.
Automatically scans active Word template and user paragraph cards for custom {{variable}} tags,
renders specialized typed input widgets (dates, times, numbers, selects, texts),
and coordinates bi-directional real-time value synchronization with paragraph cards.
"""

import os
import re
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QTimer

from services.docx_service import (
    extract_and_categorize_template_variables,
    FORBIDDEN_CONTROL_KEYWORDS,
    validate_template_variable
)
from services.template_variable_service import parse_variable_tag, get_variable_replace_pattern
from services.icon_service import get_icon, get_pixmap
from ui.components.typed_variable_input import create_typed_variable_input
from ui.components.paragraph_card import ParagraphCard


class DynamicVariablesPanel(QFrame):
    """Component for dynamically detected template variables and inputs."""

    values_applied = Signal(int)  # Number of modified paragraphs
    variable_changed = Signal(str, str)  # var_name, new_val

    def __init__(self, parent: Optional[QFrame] = None):
        super().__init__(parent)
        self.dynamic_inputs: Dict[str, Any] = {}
        self.init_ui()

    def init_ui(self):
        self.setObjectName("innerGroupFrame")
        self.setStyleSheet("""
            QFrame#innerGroupFrame {
                background-color: #faf5ff;
                border: 1.5px solid #d8b4fe;
                border-left: 5px solid #6b21a8;
                border-radius: 8px;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        # Header Bar
        h_head = QHBoxLayout()
        h_head.setSpacing(10)
        lbl_ico = QLabel()
        lbl_ico.setPixmap(get_pixmap("tag", color="#6b21a8", size=20))
        h_head.addWidget(lbl_ico)

        v_t = QVBoxLayout()
        v_t.setSpacing(2)
        self.lbl_title = QLabel("ช่องกรอกข้อมูลตัวแปรใน Template")
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #581c87;")
        self.lbl_desc = QLabel("กรอกข้อมูลตัวแปรด้านล่างนี้ ระบบจะเชื่อมต่อกับกล่องตัวแปรในย่อหน้า และนำไปแทนที่ในเอกสาร Word ให้อัตโนมัติ")
        self.lbl_desc.setStyleSheet("font-size: 13px; color: #64748b;")
        v_t.addWidget(self.lbl_title)
        v_t.addWidget(self.lbl_desc)
        h_head.addLayout(v_t)
        h_head.addStretch()

        self.btn_apply = QPushButton("นำค่าทั้งหมดไปแทนที่ในข้อความ")
        self.btn_apply.setObjectName("primaryButtonSmall")
        self.btn_apply.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btn_apply.setIcon(get_icon("check", color="#ffffff", size=14))
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #6b21a8;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #7e22ce; }
            QPushButton:pressed { background-color: #581c87; }
        """)
        self.btn_apply.setToolTip("นำข้อมูลตัวแปรที่กรอกไปแทนที่ลงในข้อความย่อหน้าทันที [Enter]")
        h_head.addWidget(self.btn_apply)
        lay.addLayout(h_head)

        lbl_dyn_tip = QLabel(
            "<b>คำแนะนำ:</b> ท่านสามารถกรอกข้อมูลตัวแปรในช่องด้านล่างนี้ หรือกรอกในกล่องชิปใต้แต่ละย่อหน้าได้โดยตรง "
            "ข้อมูลจะ<b>เชื่อมต่อถึงกันแบบเรียลไทม์</b> เมื่อกรอกแล้วสามารถกด <b>Enter</b> หรือกดปุ่ม <b>นำค่าทั้งหมดไปแทนที่ในข้อความ</b> "
            "หรือกดส่งออก Word ระบบจะนำคำจริงไปเติมในเอกสารให้อัตโนมัติ 100%"
        )
        lbl_dyn_tip.setTextFormat(Qt.TextFormat.RichText)
        lbl_dyn_tip.setWordWrap(True)
        lbl_dyn_tip.setStyleSheet(
            "font-size: 12.5px; color: #4c1d95; background: #ffffff; "
            "border: 1px solid #ddd6fe; border-radius: 6px; padding: 7px 12px; line-height: 1.45;"
        )
        lay.addWidget(lbl_dyn_tip)

        self.inputs_box = QVBoxLayout()
        self.inputs_box.setSpacing(10)
        lay.addLayout(self.inputs_box)
        self.setVisible(False)

    def scan_and_update(
        self,
        paragraph_cards: List[ParagraphCard],
        doc_type: str = "report",
        tpl_path: Optional[str] = None
    ):
        """
        Scan all paragraph cards and active Word template for custom {{variables}}.
        Dynamically generates labeled input fields with the variable name as the label.
        Automatically shows the container when variables exist, hides it when none exist.
        """
        is_compromise = (doc_type == "compromise")

        # 1. Extract variables from all paragraph cards
        card_vars = set()
        for card in paragraph_cards:
            txt = card.get_text() if hasattr(card, 'get_text') else ""
            if txt:
                matches = re.findall(
                    r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]]+?)\s*\]|\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}',
                    txt
                )
                for m1, m2, m3 in matches:
                    tag = (m1 or m2 or m3).strip()
                    clean_tag = tag.lstrip('#/').strip()
                    clean_tag = re.sub(r'^[\U0001f3f7\ufe0f\s]+', '', clean_tag).strip()
                    if clean_tag and clean_tag not in FORBIDDEN_CONTROL_KEYWORDS and not clean_tag.startswith(('#', '/')):
                        valid, _ = validate_template_variable(clean_tag)
                        if valid:
                            card_vars.add(clean_tag)

        # 2. Extract variables from active Word template
        docx_vars = set()
        if tpl_path and os.path.exists(tpl_path):
            try:
                res = extract_and_categorize_template_variables(tpl_path)
                docx_vars = set(res.get('custom_variables', []))
            except Exception:
                pass

        custom_vars = card_vars.union(docx_vars)

        # 3. Filter out system-reserved variables that are already handled in previous sections
        if is_compromise:
            comp_handled = {
                'case_black_no', 'case_red_no', 'case_subject', 'refund_total',
                'full_date', 'd', 'day', 'date', 'month', 'year', 'court',
                'court_name', 'judge_1_name', 'judge_2_name', 'plaintiff_name', 'defendant_name'
            }
            custom_vars = custom_vars - comp_handled
        else:
            report_handled = {
                'case_black_no', 'case_red_no', 'court_name', 'court', 'ชื่อศาล',
                'case_type', 'hearing_purpose', 'appointment_date', 'appointment_reason',
                'appointment_purpose', 'นัดมาทำไม', 'day', 'd', 'date', 'month', 'year',
                'hearing_time', 'plaintiff_name', 'defendant_name', 'judge_1_name',
                'judge_2_name', 'judge_๑_name', 'judge_๒_name', 'signatories',
                'attendees_summary', 'paragraphs', 'position'
            }
            custom_vars = custom_vars - report_handled

        # 4. If no custom variables found, hide container
        if not custom_vars:
            self.setVisible(False)
            self.dynamic_inputs.clear()
            return

        # 5. Preserve existing typed text and sync from paragraph cards
        current_values = {}
        for var, edt in self.dynamic_inputs.items():
            current_values[var] = edt.text().strip() if hasattr(edt, 'text') else getattr(edt, 'get_value', lambda: '')()

        for card in paragraph_cards:
            if hasattr(card, 'chip_components'):
                for c_var, comp in card.chip_components.items():
                    v = comp.get_value()
                    if v and not current_values.get(c_var):
                        current_values[c_var] = v

        # 6. Clear current dynamic widgets
        while self.inputs_box.count():
            item = self.inputs_box.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                layout = item.layout()
                if layout:
                    while layout.count():
                        sub = layout.takeAt(0)
                        if sub.widget():
                            sub.widget().deleteLater()

        self.dynamic_inputs.clear()
        sorted_vars = sorted(list(custom_vars))

        # 7. Dynamically generate rows (2 per row for balanced layout)
        row_layout = None
        for i, var_name in enumerate(sorted_vars):
            if i % 2 == 0:
                row_layout = QHBoxLayout()
                row_layout.setSpacing(14)
                self.inputs_box.addLayout(row_layout)

            v_col = QVBoxLayout()
            v_col.setSpacing(4)

            parsed = parse_variable_tag(var_name)
            display_label = parsed['name']
            if parsed['type'] == 'date' and parsed['format_style'] != 'full':
                display_label += f" ({parsed['format_style']})"

            lbl = QLabel(display_label)
            lbl.setObjectName("fieldLabel")
            lbl.setStyleSheet("font-weight: 600; color: #4c1d95; font-size: 13.5px;")
            v_col.addWidget(lbl)

            editor = create_typed_variable_input(
                parsed,
                current_values.get(var_name, ""),
                self
            )

            if hasattr(editor, 'value_changed'):
                editor.value_changed.connect(
                    lambda val, v=var_name: self.variable_changed.emit(v, val)
                )
            elif hasattr(editor, 'textChanged'):
                editor.textChanged.connect(
                    lambda val, v=var_name: self.variable_changed.emit(v, val)
                )

            v_col.addWidget(editor)
            self.dynamic_inputs[var_name] = editor

            if row_layout:
                row_layout.addLayout(v_col, 1)

        # Pad with dummy stretch if odd count
        if len(sorted_vars) % 2 != 0 and row_layout:
            row_layout.addStretch(1)

        self.setVisible(True)

    def apply_dynamic_values_to_paragraph_cards(self, paragraph_cards: List[ParagraphCard]):
        """Replace variables inside paragraph card textboxes with current panel input values."""
        replacements = {}
        for var, edt in self.dynamic_inputs.items():
            val = edt.text().strip() if hasattr(edt, 'text') else getattr(edt, 'get_value', lambda: '')()
            if val:
                replacements[var] = val
                base_n = parse_variable_tag(var)['name']
                replacements[base_n] = val

        for card in paragraph_cards:
            if hasattr(card, 'chip_components'):
                for var, comp in card.chip_components.items():
                    val = comp.get_value()
                    if val and var not in replacements:
                        replacements[var] = val
                        base_n = getattr(comp, 'base_name', parse_variable_tag(var)['name'])
                        replacements[base_n] = val

        if not replacements:
            return

        count_modified = 0
        for card in paragraph_cards:
            text = card.get_text()
            original = text
            for var, val in replacements.items():
                base_n = parse_variable_tag(var)['name']
                pat = get_variable_replace_pattern(base_n)
                text = pat.sub(val, text)
            if text != original:
                card.set_text(text)
                count_modified += 1

        if count_modified > 0:
            b = self.btn_apply
            b.setText(f"แทนที่เรียบร้อย ({count_modified} ย่อหน้า)")
            b.setIcon(get_icon("check", color="#ffffff", size=14))
            b.setStyleSheet("background-color: #16a34a; color: #ffffff; border: none; border-radius: 5px; padding: 6px 14px; font-size: 13px; font-weight: 600;")
            QTimer.singleShot(2000, lambda: (
                b.setText("นำค่าทั้งหมดไปแทนที่ในข้อความ"),
                b.setIcon(get_icon("check", color="#ffffff", size=14)),
                b.setStyleSheet("background-color: #6b21a8; color: #ffffff; border: none; border-radius: 5px; padding: 6px 14px; font-size: 13px; font-weight: 600;")
            ))
            self.values_applied.emit(count_modified)

    def get_dynamic_values(self) -> Dict[str, str]:
        values = {}
        for var, edt in self.dynamic_inputs.items():
            val = edt.text().strip() if hasattr(edt, 'text') else getattr(edt, 'get_value', lambda: '')()
            if val:
                values[var] = val
                base_n = parse_variable_tag(var)['name']
                values[base_n] = val
        return values

    def sync_var_from_card(self, var_name: str, new_val: str):
        """Synchronize variable value from card chip to panel input field."""
        if var_name in self.dynamic_inputs:
            comp = self.dynamic_inputs[var_name]
            cur = comp.text() if hasattr(comp, 'text') else getattr(comp, 'get_value', lambda: '')()
            if cur != new_val:
                if hasattr(comp, 'set_value'):
                    comp.set_value(new_val)
                elif hasattr(comp, 'setText'):
                    comp.setText(new_val)
