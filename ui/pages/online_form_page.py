"""
Page 3 (Online): 3-Section Sequential Wizard Workflow for Online Court Proceedings Report
Section 1: Case Information & Bench Judges Pairing
Section 2: Online Platform & Signatories / Attendees Ordering
Section 3: Optional Paragraphs & Online Word Document Generator (.docx)

Modularized architecture utilizing dedicated sub-components in `ui.components.form_sections`.
"""

import os
import re
import subprocess
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QMessageBox, QStackedWidget,
    QFileDialog, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal

from constants import DEFAULT_CASE_TYPES
from services.excel_service import to_full_buddhist_year
from services.docx_service import (
    generate_online_report_docx,
    format_online_attendees_summary
)
from services.template_variable_service import parse_variable_tag, get_variable_replace_pattern
from services import storage_service
from services.icon_service import get_icon
from ui.dialogs.template_select_dialog import TemplateSelectDialog
from ui.components.online_signatories_manager import OnlineSignatoriesManagerWidget
from ui.components.form_sections import (
    CaseInfoSectionWidget,
    BenchPairingWidget,
    ParagraphsSectionWidget,
    DynamicVariablesPanel
)
from ui.components.paragraph_card import ParagraphCard


class OnlineFormPage(QWidget):
    """Step 4: Dedicated 3-section form for Online Court Proceedings Report."""

    back_to_doc_type_requested = Signal()
    back_to_table_requested = Signal()
    bench_manager_requested = Signal()
    court_saved_as_default = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.doc_type: str = "report_online"
        self.form_section: int = 0
        self.case_types_list: List[str] = list(DEFAULT_CASE_TYPES)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 20, 32, 20)
        layout.setSpacing(14)

        # -------------------------------------------------------------
        # Header Bar
        # -------------------------------------------------------------
        header_layout = QHBoxLayout()
        self.lbl_page_title = QLabel("ขั้นตอนที่ 4: จัดทำรายงานกระบวนพิจารณาคดี (แบบออนไลน์)")
        self.lbl_page_title.setObjectName("stepPageTitle")
        header_layout.addWidget(self.lbl_page_title)
        header_layout.addStretch()

        btn_back_doctype = QPushButton("เปลี่ยนประเภทเอกสาร")
        btn_back_doctype.setObjectName("secondaryButton")
        btn_back_doctype.setIcon(get_icon("arrow-left", color="#4c1d95", size=15))
        btn_back_doctype.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 7px 14px; font-weight: 500; font-size: 13.5px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_back_doctype.setToolTip("ย้อนกลับไปยังขั้นตอนเลือกประเภทเอกสาร [PgUp]")
        btn_back_doctype.clicked.connect(self.back_to_doc_type_requested.emit)
        header_layout.addWidget(btn_back_doctype)

        btn_back_table = QPushButton("เปลี่ยนคดี (กลับตาราง)")
        btn_back_table.setObjectName("secondaryButton")
        btn_back_table.setIcon(get_icon("rotate-ccw", color="#4c1d95", size=15))
        btn_back_table.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 7px 14px; font-weight: 500; font-size: 13.5px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_back_table.setToolTip("กลับไปยังตารางเลือกคดี")
        btn_back_table.clicked.connect(self.back_to_table_requested.emit)
        header_layout.addWidget(btn_back_table)
        layout.addLayout(header_layout)

        # -------------------------------------------------------------
        # Section Stepper Tabs (Breadcrumbs)
        # -------------------------------------------------------------
        stepper_bar = QHBoxLayout()
        stepper_bar.setSpacing(10)

        self.btn_sec_tab1 = QPushButton("1. ข้อมูลคดี & องค์คณะ")
        self.btn_sec_tab1.setObjectName("stepperTabButton")
        self.btn_sec_tab1.setIcon(get_icon("file-text", color="#4c1d95", size=16))
        self.btn_sec_tab1.clicked.connect(lambda: self.set_form_section(0))
        stepper_bar.addWidget(self.btn_sec_tab1)

        self.btn_sec_tab2 = QPushButton("2. รายชื่อผู้มาศาล (ออนไลน์)")
        self.btn_sec_tab2.setObjectName("stepperTabButton")
        self.btn_sec_tab2.setIcon(get_icon("users", color="#4c1d95", size=16))
        self.btn_sec_tab2.clicked.connect(lambda: self.set_form_section(1))
        stepper_bar.addWidget(self.btn_sec_tab2)

        self.btn_sec_tab3 = QPushButton("3. ย่อหน้ากระบวนพิจารณา & สร้างรายงาน")
        self.btn_sec_tab3.setObjectName("stepperTabButton")
        self.btn_sec_tab3.setIcon(get_icon("scale", color="#4c1d95", size=16))
        self.btn_sec_tab3.clicked.connect(lambda: self.set_form_section(2))
        stepper_bar.addWidget(self.btn_sec_tab3)
        layout.addLayout(stepper_bar)

        # -------------------------------------------------------------
        # Sub Stacked Widget (3 Distinct Sequential Sections)
        # -------------------------------------------------------------
        self.form_sub_stack = QStackedWidget()
        self.form_sub_stack.setObjectName("formSubStack")

        # =============================================================
        # SUB-PAGE 0 (Section 1: ข้อมูลคดีความและองค์คณะ)
        # =============================================================
        self.page_sec1 = QWidget()
        sec1_vbox = QVBoxLayout(self.page_sec1)
        sec1_vbox.setContentsMargins(0, 0, 0, 0)
        sec1_vbox.setSpacing(12)

        scroll_sec1 = QScrollArea()
        scroll_sec1.setWidgetResizable(True)
        scroll_sec1.setObjectName("scrollArea")
        container_sec1 = QWidget()
        lay_sec1 = QVBoxLayout(container_sec1)
        lay_sec1.setContentsMargins(18, 16, 18, 16)
        lay_sec1.setSpacing(18)

        # 1.1 Case Info Component
        self.case_info_widget = CaseInfoSectionWidget(self.case_types_list, self)
        self.case_info_widget.court_saved_as_default.connect(self.court_saved_as_default.emit)
        lay_sec1.addWidget(self.case_info_widget)

        # 1.2 Bench Pairing Component
        self.bench_widget = BenchPairingWidget(self)
        self.bench_widget.bench_manager_requested.connect(self.bench_manager_requested.emit)
        lay_sec1.addWidget(self.bench_widget)
        lay_sec1.addStretch()

        scroll_sec1.setWidget(container_sec1)
        sec1_vbox.addWidget(scroll_sec1)

        # Bottom Bar Section 1
        sec1_bottom = QHBoxLayout()
        btn_sec1_back = QPushButton("กลับตารางเลือกคดี")
        btn_sec1_back.setObjectName("secondaryButton")
        btn_sec1_back.setIcon(get_icon("arrow-left", color="#4c1d95", size=16))
        btn_sec1_back.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 9px 16px; font-weight: 500; font-size: 14px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_sec1_back.setToolTip("ย้อนกลับตารางเลือกคดี [PgUp]")
        btn_sec1_back.clicked.connect(self.back_to_table_requested.emit)
        sec1_bottom.addWidget(btn_sec1_back)
        sec1_bottom.addStretch()

        self.btn_sec1_next = QPushButton("ต่อไป: เลือกรายชื่อผู้มาศาล (ออนไลน์)")
        self.btn_sec1_next.setObjectName("primaryButtonLarge")
        self.btn_sec1_next.setIcon(get_icon("arrow-right", color="#ffffff", size=16))
        self.btn_sec1_next.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; padding: 13px 30px; font-size: 16px; font-weight: 600; border-radius: 8px; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; } "
            "QPushButton:pressed { background-color: #3b0764; }"
        )
        self.btn_sec1_next.setToolTip("ไปยังขั้นตอนเลือกรายชื่อผู้มาศาล [PgDown]")
        self.btn_sec1_next.clicked.connect(self.handle_next_to_attendees)
        sec1_bottom.addWidget(self.btn_sec1_next)
        sec1_vbox.addLayout(sec1_bottom)

        self.form_sub_stack.addWidget(self.page_sec1)

        # =============================================================
        # SUB-PAGE 1 (Section 2: เลือกรายชื่อผู้มาศาลแบบออนไลน์)
        # =============================================================
        self.page_sec2 = QWidget()
        sec2_vbox = QVBoxLayout(self.page_sec2)
        sec2_vbox.setContentsMargins(0, 0, 0, 0)
        sec2_vbox.setSpacing(10)

        scroll_sec2 = QScrollArea()
        scroll_sec2.setWidgetResizable(True)
        scroll_sec2.setObjectName("scrollArea")
        scroll_sec2.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container_sec2 = QWidget()
        lay_sec2 = QVBoxLayout(container_sec2)
        lay_sec2.setContentsMargins(12, 6, 12, 6)
        lay_sec2.setSpacing(8)

        self.signatories_widget = OnlineSignatoriesManagerWidget()
        self.signatories_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lay_sec2.addWidget(self.signatories_widget, 1)

        scroll_sec2.setWidget(container_sec2)
        sec2_vbox.addWidget(scroll_sec2, 1)

        # Bottom Bar Section 2
        sec2_bottom = QHBoxLayout()
        btn_sec2_back = QPushButton("ย้อนกลับ: ข้อมูลคดี")
        btn_sec2_back.setObjectName("secondaryButton")
        btn_sec2_back.setIcon(get_icon("arrow-left", color="#4c1d95", size=16))
        btn_sec2_back.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 9px 16px; font-weight: 500; font-size: 14px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_sec2_back.setToolTip("ย้อนกลับไปยังข้อมูลคดี [PgUp]")
        btn_sec2_back.clicked.connect(lambda: self.set_form_section(0))
        sec2_bottom.addWidget(btn_sec2_back)
        sec2_bottom.addStretch()

        btn_sec2_next = QPushButton("ต่อไป: ย่อหน้ากระบวนพิจารณา")
        btn_sec2_next.setObjectName("primaryButtonLarge")
        btn_sec2_next.setIcon(get_icon("arrow-right", color="#ffffff", size=16))
        btn_sec2_next.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; padding: 13px 30px; font-size: 16px; font-weight: 600; border-radius: 8px; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; } "
            "QPushButton:pressed { background-color: #3b0764; }"
        )
        btn_sec2_next.setToolTip("ไปยังขั้นตอนย่อหน้ากระบวนพิจารณา [PgDown]")
        btn_sec2_next.clicked.connect(lambda: self.set_form_section(2))
        sec2_bottom.addWidget(btn_sec2_next)
        sec2_vbox.addLayout(sec2_bottom)

        self.form_sub_stack.addWidget(self.page_sec2)

        # =============================================================
        # SUB-PAGE 2 (Section 3: ย่อหน้ากระบวนพิจารณา & สร้างรายงาน Word ออนไลน์)
        # =============================================================
        self.page_sec3 = QWidget()
        sec3_vbox = QVBoxLayout(self.page_sec3)
        sec3_vbox.setContentsMargins(0, 0, 0, 0)
        sec3_vbox.setSpacing(12)

        scroll_sec3 = QScrollArea()
        scroll_sec3.setWidgetResizable(True)
        scroll_sec3.setObjectName("scrollArea")
        container_sec3 = QWidget()
        lay_sec3 = QVBoxLayout(container_sec3)
        lay_sec3.setContentsMargins(18, 16, 18, 16)
        lay_sec3.setSpacing(14)

        # Dynamic Variables Panel (headless/hidden to avoid redundant top panel)
        self.dynamic_variables_panel = DynamicVariablesPanel(self)
        self.dynamic_variables_panel.setVisible(False)
        self.dynamic_variables_panel.btn_apply.clicked.connect(self.apply_dynamic_values_to_paragraph_cards)
        self.dynamic_variables_panel.variable_changed.connect(self._sync_var_to_cards)

        # Paragraphs Management Component
        self.paragraphs_widget = ParagraphsSectionWidget(self)
        self.paragraphs_widget.template_select_requested.connect(self.handle_add_paragraph_from_template)
        self.paragraphs_widget.paragraphs_changed.connect(self.scan_and_update_dynamic_fields)
        self.paragraphs_widget.chip_value_changed.connect(self._sync_var_from_card)
        lay_sec3.addWidget(self.paragraphs_widget)
        lay_sec3.addStretch()

        scroll_sec3.setWidget(container_sec3)
        sec3_vbox.addWidget(scroll_sec3)

        # Bottom Bar Section 3
        sec3_bottom = QHBoxLayout()
        btn_sec3_back = QPushButton("ย้อนกลับ: รายชื่อผู้มาศาล (ออนไลน์)")
        btn_sec3_back.setObjectName("secondaryButton")
        btn_sec3_back.setIcon(get_icon("arrow-left", color="#4c1d95", size=16))
        btn_sec3_back.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 9px 16px; font-weight: 500; font-size: 14px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_sec3_back.setToolTip("ย้อนกลับไปยังรายชื่อผู้มาศาล [PgUp]")
        btn_sec3_back.clicked.connect(lambda: self.set_form_section(1))
        sec3_bottom.addWidget(btn_sec3_back)
        sec3_bottom.addStretch()

        btn_check_tpl = QPushButton("ตรวจสอบ/กู้คืนแม่แบบ Word ออนไลน์")
        btn_check_tpl.setObjectName("secondaryButton")
        btn_check_tpl.setIcon(get_icon("file-text", color="#4c1d95", size=16))
        btn_check_tpl.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #d8b4fe;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
            }
        """)
        btn_check_tpl.setToolTip("ตรวจสอบความถูกต้องของไฟล์แม่แบบ Word หรือกู้คืนแม่แบบต้นฉบับ")
        btn_check_tpl.clicked.connect(lambda: self.handle_check_or_recover_template("online_report"))
        sec3_bottom.addWidget(btn_check_tpl)

        self.btn_generate = QPushButton("สร้างรายงานกระบวนพิจารณาออนไลน์ (.docx)")
        self.btn_generate.setObjectName("generateButton")
        self.btn_generate.setIcon(get_icon("file-text", color="#ffffff", size=18))
        self.btn_generate.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; padding: 11px 26px; font-size: 15px; font-weight: 600; border-radius: 6px; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; } "
            "QPushButton:pressed { background-color: #3b0764; }"
        )
        self.btn_generate.setToolTip("สร้างไฟล์รายงานกระบวนพิจารณาออนไลน์ (.docx) [Ctrl+S หรือ F5]")
        self.btn_generate.clicked.connect(self.handle_generate_docx)
        sec3_bottom.addWidget(self.btn_generate)
        sec3_vbox.addLayout(sec3_bottom)

        self.form_sub_stack.addWidget(self.page_sec3)
        layout.addWidget(self.form_sub_stack)

        # -------------------------------------------------------------
        # Backward Compatibility Field Aliases
        # -------------------------------------------------------------
        self.txt_case_black = self.case_info_widget.txt_case_black
        self.txt_case_red = self.case_info_widget.txt_case_red
        self.txt_court_name = self.case_info_widget.txt_court_name
        self.txt_case_type = self.case_info_widget.txt_case_type
        self.txt_hearing_purpose = self.case_info_widget.txt_hearing_purpose
        self.txt_day = self.case_info_widget.txt_day
        self.txt_month = self.case_info_widget.txt_month
        self.txt_year = self.case_info_widget.txt_year
        self.txt_time = self.case_info_widget.txt_time
        self.txt_plaintiff = self.case_info_widget.txt_plaintiff
        self.txt_defendant = self.case_info_widget.txt_defendant

        self.txt_judge1 = self.bench_widget.txt_judge1
        self.txt_judge2 = self.bench_widget.txt_judge2
        self.lbl_bench_status = self.bench_widget.lbl_bench_status

        self.group_dyn_fields = self.dynamic_variables_panel

    # -------------------------------------------------------------------------
    # Backward Compatibility Properties & Delegates
    # -------------------------------------------------------------------------
    @property
    def cmb_judge1(self):
        return self.bench_widget.cmb_judge1

    @property
    def paragraph_cards(self) -> List[ParagraphCard]:
        return self.paragraphs_widget.paragraph_cards

    @property
    def dynamic_inputs(self) -> Dict[str, Any]:
        return self.dynamic_variables_panel.dynamic_inputs

    # -------------------------------------------------------------------------
    # Lifecycle & Navigation Events
    # -------------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_judge1_completer()
        if not self.txt_court_name.text().strip():
            self.refresh_default_court()
        self.focus_first_field()

    def hideEvent(self, event):
        super().hideEvent(event)
        if hasattr(self, 'txt_case_type') and hasattr(self.txt_case_type, 'hide_popup'):
            self.txt_case_type.hide_popup()

    def set_form_section(self, idx: int):
        self.form_section = idx
        if hasattr(self, 'form_sub_stack'):
            if idx == 0 and hasattr(self, 'page_sec1'):
                self.form_sub_stack.setCurrentWidget(self.page_sec1)
            elif idx == 1 and hasattr(self, 'page_sec2'):
                self.form_sub_stack.setCurrentWidget(self.page_sec2)
            elif idx == 2 and hasattr(self, 'page_sec3'):
                self.scan_and_update_dynamic_fields()
                self.form_sub_stack.setCurrentWidget(self.page_sec3)

        for i, btn in enumerate([self.btn_sec_tab1, self.btn_sec_tab2, self.btn_sec_tab3]):
            btn.setProperty("active", i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.focus_first_field()

    def focus_first_field(self):
        if not self.isVisible():
            return
        if self.form_section == 0:
            self.case_info_widget.focus_first_empty_field()
        elif self.form_section == 1:
            if hasattr(self, 'signatories_widget'):
                self.signatories_widget.setFocus()
        elif self.form_section == 2:
            if self.paragraph_cards:
                card0 = self.paragraph_cards[0]
                if hasattr(card0, 'txt_editor'):
                    card0.txt_editor.setFocus()
                elif hasattr(card0, 'txt_content'):
                    card0.txt_content.setFocus()
            elif hasattr(self, 'btn_generate'):
                self.btn_generate.setFocus()

    def handle_next_to_attendees(self):
        self.bench_widget.confirm_bench_pair_if_needed()
        self.set_form_section(1)

    # -------------------------------------------------------------------------
    # Delegation to Sub-Components
    # -------------------------------------------------------------------------
    def update_case_types(self, new_types: List[str]):
        self.case_types_list = list(new_types)
        self.case_info_widget.update_case_types(new_types)

    def load_case_row(self, row: Dict[str, Any], mapping: Dict[str, str]):
        self.case_info_widget.load_case_row(row, mapping)
        self.bench_widget.load_bench_data(row, mapping)

    def save_current_court_as_default(self):
        self.case_info_widget.save_current_court_as_default()

    def refresh_default_court(self):
        self.case_info_widget.refresh_default_court()

    def refresh_judge1_completer(self):
        self.bench_widget.refresh_completers()

    def handle_judge1_changed(self, text: str):
        self.bench_widget.handle_judge1_changed(text)

    def handle_save_current_pairing(self):
        self.bench_widget.handle_save_current_pairing()

    def confirm_bench_pair_if_needed(self):
        return self.bench_widget.confirm_bench_pair_if_needed()

    def update_bench_status(self, text: str, style: str = ""):
        self.bench_widget.update_bench_status(text, style)

    def add_paragraph_card(self, initial_text: str = "") -> ParagraphCard:
        card = self.paragraphs_widget.add_paragraph_card(initial_text)
        self.scan_and_update_dynamic_fields()
        return card

    def reorder_paragraph_cards(self, src_idx: int, target_idx: int):
        self.paragraphs_widget.reorder_paragraph_cards(src_idx, target_idx)

    def handle_add_paragraph_from_template(self):
        dlg = TemplateSelectDialog(self)
        if dlg.exec() and dlg.selected_content:
            self.add_paragraph_card(dlg.selected_content)

    def move_paragraph_up(self, card: ParagraphCard):
        self.paragraphs_widget.move_paragraph_up(card)

    def move_paragraph_down(self, card: ParagraphCard):
        self.paragraphs_widget.move_paragraph_down(card)

    def delete_paragraph_card(self, card: ParagraphCard):
        self.paragraphs_widget.delete_paragraph_card(card)

    def rebuild_paragraph_layout(self):
        self.paragraphs_widget.rebuild_paragraph_layout()

    def refresh_paragraph_indices(self):
        self.paragraphs_widget.refresh_paragraph_indices()

    # -------------------------------------------------------------------------
    # Dynamic Variables Sync Logic
    # -------------------------------------------------------------------------
    def get_active_template_path(self) -> Optional[str]:
        tpl_dir = storage_service.get_templates_dir()
        if not tpl_dir or not os.path.exists(tpl_dir):
            return None

        # Prioritize exact names for online court report
        candidates = [
            "รายงานกระบวนพิจารณาออนใลน์.docx",
            "รายงานกระบวนพิจารณาออนไลน์.docx",
            "template_online.docx",
            "online.docx"
        ]
        for c in candidates:
            p = os.path.join(tpl_dir, c)
            if os.path.exists(p):
                return p

        # Fallback search specifically for online report file (NEVER pick normal report)
        for f in os.listdir(tpl_dir):
            if f.endswith(".docx") and not f.startswith("~$"):
                f_lower = f.lower()
                if "ออนใลน์" in f or "ออนไลน์" in f or "online" in f_lower or "อิเล็กทรอนิกส์" in f:
                    return os.path.join(tpl_dir, f)
        return None

    def scan_and_update_dynamic_fields(self):
        tpl_path = self.get_active_template_path()
        self.dynamic_variables_panel.scan_and_update(self.paragraph_cards, self.doc_type, tpl_path)
        self.dynamic_variables_panel.setVisible(False)

    def apply_dynamic_values_to_paragraph_cards(self):
        self.dynamic_variables_panel.apply_dynamic_values_to_paragraph_cards(self.paragraph_cards)
        self.scan_and_update_dynamic_fields()

    def _sync_var_to_cards(self, var_name: str, new_val: str):
        for card in self.paragraph_cards:
            if hasattr(card, 'chip_components') and var_name in card.chip_components:
                comp = card.chip_components[var_name]
                if comp.get_value() != new_val:
                    comp.set_value(new_val)

    def _sync_var_from_card(self, var_name: str, new_val: str):
        self.dynamic_variables_panel.sync_var_from_card(var_name, new_val)

    # -------------------------------------------------------------------------
    # Document Generation
    # -------------------------------------------------------------------------
    def trigger_generate_document(self):
        self.handle_generate_docx()

    def handle_generate_docx(self):
        case_black = self.txt_case_black.text().strip()
        if not case_black:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุคดีหมายเลขดำที่ในแบบฟอร์ม")
            self.set_form_section(0)
            self.txt_case_black.setFocus()
            return

        tpl_path = self.get_active_template_path()
        if not tpl_path or not os.path.exists(tpl_path):
            tpl_dir = storage_service.get_templates_dir()
            QMessageBox.critical(
                self, "ข้อผิดพลาด",
                f"ไม่พบไฟล์ Template Word สำหรับรายงานออนไลน์ (.docx) ในโฟลเดอร์:\n{tpl_dir}\n\nต้องการไฟล์: 'รายงานกระบวนพิจารณาออนใลน์.docx' หรือ 'รายงานกระบวนพิจารณาออนไลน์.docx'"
            )
            return

        from services.template_recovery_service import validate_word_template, restore_word_template
        v_res = validate_word_template(tpl_path, "online_report")
        if not v_res["valid"] and v_res.get("status_level") == "error":
            missing_items = []
            for ml in v_res.get("missing_loops", []):
                missing_items.append(f"• {ml['issue']} ({ml['start_tag']} ... {ml['end_tag']})")
            for se in v_res.get("syntax_errors", []):
                missing_items.append(f"• {se}")
            missing_text = "\n".join(missing_items) if missing_items else v_res["status_message"]

            reply = QMessageBox.warning(
                self, "แม่แบบเอกสารไม่สมบูรณ์",
                f"ไฟล์แม่แบบ '{v_res['filename']}' ตรวจพบข้อผิดพลาดที่ไม่สามารถสร้างเอกสารได้:\n\n"
                f"{missing_text}\n\n"
                f"ท่านต้องการให้ระบบกู้คืนแม่แบบเป็นค่าเริ่มต้นของโปรแกรมเดี๋ยวนี้หรือไม่?\n"
                f"(ระบบจะสำรองไฟล์ปัจจุบันที่ท่านแก้ไขไว้ใน templates/backup/ ให้อัตโนมัติ)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                ok, msg, bkp = restore_word_template(v_res["filename"])
                if ok:
                    QMessageBox.information(self, "กู้คืนแม่แบบสำเร็จ", f"{msg}\n\nระบบจะเริ่มสร้างเอกสารต่อให้ทันทีครับ")
                    tpl_path = self.get_active_template_path()
                else:
                    QMessageBox.critical(self, "กู้คืนล้มเหลว", msg)
                    return
            else:
                return

        safe_black = re.sub(r'[\\/*?:"<>|]', '-', case_black)
        default_filename = f"รายงานกระบวนพิจารณาออนไลน์_{safe_black}.docx"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "บันทึกรายงานกระบวนพิจารณาออนไลน์ (.docx)", default_filename, "Word Document (*.docx)"
        )
        if not save_path:
            return

        dyn_replacements = self.dynamic_variables_panel.get_dynamic_values()

        raw_paragraphs = []
        for card in self.paragraph_cards:
            txt = card.get_text()
            if not txt:
                continue

            card_vals = {}
            if hasattr(card, 'chip_components'):
                for c_var, comp in card.chip_components.items():
                    val = comp.get_value()
                    if val:
                        card_vals[c_var] = val
            elif hasattr(card, 'var_inputs'):
                for c_var, inp in card.var_inputs.items():
                    val = inp.text().strip() if hasattr(inp, 'text') else getattr(inp, 'get_value', lambda: '')()
                    if val:
                        card_vals[c_var] = val

            combined_replacements = {**card_vals, **{k: v for k, v in dyn_replacements.items() if v}}

            for var_name, val in combined_replacements.items():
                if val:
                    base_n = parse_variable_tag(var_name)['name']
                    pat = get_variable_replace_pattern(base_n)
                    txt = pat.sub(val, txt)
            raw_paragraphs.append(txt)

        signatories_data = self.signatories_widget.get_signatories()
        meeting_platform = self.signatories_widget.get_platform()
        attendees_summary = format_online_attendees_summary(signatories_data, platform=meeting_platform)

        data = {
            'case_black_no': case_black,
            'case_red_no': self.txt_case_red.text().strip(),
            'court_name': self.txt_court_name.text().strip(),
            'case_type': self.txt_case_type.text().strip(),
            'hearing_purpose': self.txt_hearing_purpose.text().strip(),
            'appointment_date': self.txt_hearing_purpose.text().strip(),
            'appointment_reason': self.txt_hearing_purpose.text().strip(),
            'appointment_purpose': self.txt_hearing_purpose.text().strip(),
            'นัดมาทำไม': self.txt_hearing_purpose.text().strip(),
            'day': self.txt_day.text().strip(),
            'date': self.txt_day.text().strip(),
            'month': self.txt_month.text().strip(),
            'year': to_full_buddhist_year(self.txt_year.text().strip()) if self.txt_year.text().strip() else "",
            'hearing_time': self.txt_time.text().strip(),
            'plaintiff_name': self.txt_plaintiff.text().strip(),
            'defendant_name': self.txt_defendant.text().strip(),
            'judge_1_name': self.txt_judge1.text().strip(),
            'judge_2_name': self.txt_judge2.text().strip(),
            'signatories': signatories_data,
            'attendees_summary': attendees_summary,
            'paragraphs': raw_paragraphs,
        }

        # Inject custom variables
        for var_name, val in dyn_replacements.items():
            if val:
                data[var_name] = val
                data[parse_variable_tag(var_name)['name']] = val
        for card in self.paragraph_cards:
            if hasattr(card, 'chip_components'):
                for c_var, comp in card.chip_components.items():
                    val = comp.get_value()
                    if val and (c_var not in data or not data[c_var]):
                        data[c_var] = val
                        data[parse_variable_tag(c_var)['name']] = val

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                generate_online_report_docx(tpl_path, save_path, data)
            finally:
                while QApplication.overrideCursor():
                    QApplication.restoreOverrideCursor()

            reply = QMessageBox.information(
                self, "สร้างเอกสารสำเร็จ",
                f"สร้างรายงานกระบวนพิจารณาออนไลน์เรียบร้อยแล้ว:\n{save_path}\n\nท่านต้องการเปิดโฟลเดอร์ที่เก็บไฟล์หรือไม่?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                norm_file = os.path.normpath(os.path.abspath(save_path))
                if os.path.exists(norm_file):
                    try:
                        subprocess.Popen(['explorer', f'/select,{norm_file}'])
                    except Exception:
                        folder = os.path.dirname(norm_file)
                        os.startfile(folder)
                else:
                    folder = os.path.dirname(norm_file)
                    if os.path.exists(folder):
                        os.startfile(folder)
        except PermissionError:
            QMessageBox.critical(
                self, "ไม่สามารถบันทึกเอกสารได้",
                f"ไม่สามารถเขียนทับไฟล์ได้:\n{save_path}\n\nกรุณาปิดโปรแกรม Microsoft Word ที่เปิดไฟล์นี้อยู่ แล้วลองใหม่อีกครั้ง"
            )
        except Exception as e:
            QMessageBox.critical(self, "เกิดข้อผิดพลาด", f"ไม่สามารถสร้างเอกสารได้:\n{str(e)}")

    def has_unsaved_content(self) -> bool:
        """Check if user has modified form data or added non-empty paragraphs."""
        for card in self.paragraph_cards:
            if hasattr(card, 'get_text') and card.get_text().strip():
                return True
        if hasattr(self, 'txt_case_black') and self.txt_case_black.text().strip():
            return True
        return False

    def get_tutorial_steps(self):
        """Return tutorial steps for Step 4 (Online Form Page)."""
        from ui.components.tutorial_overlay import TutorialStep
        return [
            TutorialStep(
                target=self.txt_judge1,
                title="ระบบองค์คณะผู้พิพากษา (Bench Pairing)",
                description="พิมพ์หรือเลือกชื่อผู้พิพากษาเจ้าของสำนวน เมื่อระบบพบประวัติการจับคู่ ระบบจะเติมชื่อผู้พิพากษาองค์คณะคนที่ 2 ให้อัตโนมัติ",
                preferred_position="bottom"
            ),
            TutorialStep(
                target=self.btn_sec_tab2,
                title="แท็บที่ 2: รายชื่อผู้มาศาลแบบออนไลน์",
                description="สำหรับเลือกช่องทางการประชุม (เช่น Google Meet, Zoom) และติ๊กช่อง 'ออนไลน์' สำหรับผู้มาศาลที่เข้าร่วมผ่านภาพและเสียง",
                preferred_position="bottom"
            ),
            TutorialStep(
                target=self.btn_sec_tab3,
                title="แท็บที่ 3: ข้อความย่อหน้า & ออกเอกสารออนไลน์",
                description="สำหรับพิมพ์หรือดึงข้อความจากแม่แบบ และกดสร้างไฟล์ Word ออนไลน์ (.docx) ฉบับสมบูรณ์ (หรือกดคีย์ลัด Ctrl+S)",
                preferred_position="bottom"
            )
        ]

    def handle_check_or_recover_template(self, tpl_key: str = "online_report"):
        from ui.dialogs.template_recovery_dialog import TemplateRecoveryDialog
        dlg = TemplateRecoveryDialog(self, initial_tpl_key=tpl_key)
        dlg.exec()
        self.scan_and_update_dynamic_fields()
