"""
Page 3: 3-Section Sequential Wizard Workflow
Section 1: Case Information & Bench Judges Pairing
Section 2: Signatories / Attendees Ordering
Section 3: Optional Paragraphs & Word Document Generator

Modularized architecture utilizing dedicated sub-components in `ui.components.form_sections`.
"""

import os
import re
import subprocess
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QMessageBox,
    QStackedWidget, QFileDialog, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal

from constants import DEFAULT_CASE_TYPES
from services.excel_service import to_full_buddhist_year
from services.docx_service import (
    generate_report_docx,
    generate_compromise_docx,
    format_attendees_summary
)
from services.template_variable_service import parse_variable_tag, get_variable_replace_pattern
from services import storage_service
from services.icon_service import get_icon
from ui.dialogs.template_select_dialog import TemplateSelectDialog
from ui.components.signatories_manager import SignatoriesManagerWidget
from ui.components.form_sections import (
    CaseInfoSectionWidget,
    BenchPairingWidget,
    CompromiseDetailsWidget,
    ParagraphsSectionWidget,
    DynamicVariablesPanel
)
from ui.components.paragraph_card import ParagraphCard


class FormPage(QWidget):
    """Step 3/4: Comprehensive modular form wizard for case details, attendees, and document generation."""

    back_to_doc_type_requested = Signal()
    back_to_table_requested = Signal()
    bench_manager_requested = Signal()
    court_saved_as_default = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.doc_type: str = "report"
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
        self.lbl_page_title = QLabel("ขั้นตอนที่ 4: จัดทำรายงานกระบวนพิจารณาคดี")
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

        self.btn_sec_tab2 = QPushButton("2. รายชื่อผู้มาศาล")
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
        # Sub Stacked Widget (Sequential Sections)
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

        self.btn_sec1_next = QPushButton("ต่อไป: เลือกรายชื่อผู้มาศาล")
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
        # SUB-PAGE 1 (Section 2: เลือกรายชื่อผู้มาศาลสำหรับรายงาน)
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

        self.signatories_widget = SignatoriesManagerWidget()
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
        # SUB-PAGE 2 (Section 3: ย่อหน้ากระบวนพิจารณา & สร้างรายงาน Word)
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

        # Dynamic Template Variables Panel (headless/hidden to avoid redundant top panel)
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
        btn_sec3_back = QPushButton("ย้อนกลับ: รายชื่อผู้มาศาล")
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

        btn_check_tpl = QPushButton("ตรวจสอบ/กู้คืนแม่แบบ Word")
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
        btn_check_tpl.clicked.connect(lambda: self.handle_check_or_recover_template("report"))
        sec3_bottom.addWidget(btn_check_tpl)

        self.btn_generate = QPushButton("สร้างรายงานกระบวนพิจารณา (.docx)")
        self.btn_generate.setObjectName("generateButton")
        self.btn_generate.setIcon(get_icon("file-text", color="#ffffff", size=18))
        self.btn_generate.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; padding: 11px 26px; font-size: 15px; font-weight: 600; border-radius: 6px; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; } "
            "QPushButton:pressed { background-color: #3b0764; }"
        )
        self.btn_generate.setToolTip("สร้างไฟล์รายงานกระบวนพิจารณา (.docx) [Ctrl+S หรือ F5]")
        self.btn_generate.clicked.connect(self.handle_generate_docx)
        sec3_bottom.addWidget(self.btn_generate)
        sec3_vbox.addLayout(sec3_bottom)

        self.form_sub_stack.addWidget(self.page_sec3)

        # =============================================================
        # SUB-PAGE 3 (Compromise Section 2: ข้อมูลสัญญาประนีประนอมยอมความ)
        # =============================================================
        self.page_sec2_compromise = QWidget()
        sec2_comp_vbox = QVBoxLayout(self.page_sec2_compromise)
        sec2_comp_vbox.setContentsMargins(0, 0, 0, 0)
        sec2_comp_vbox.setSpacing(12)

        scroll_sec2_comp = QScrollArea()
        scroll_sec2_comp.setWidgetResizable(True)
        scroll_sec2_comp.setObjectName("scrollArea")
        container_sec2_comp = QWidget()
        lay_sec2_comp = QVBoxLayout(container_sec2_comp)
        lay_sec2_comp.setContentsMargins(18, 16, 18, 16)
        lay_sec2_comp.setSpacing(18)

        # Compromise Details Component
        self.compromise_widget = CompromiseDetailsWidget(self)
        self.compromise_widget.connect_case_date_button(self.fill_compromise_date_from_excel)
        lay_sec2_comp.addWidget(self.compromise_widget)
        lay_sec2_comp.addStretch()

        scroll_sec2_comp.setWidget(container_sec2_comp)
        sec2_comp_vbox.addWidget(scroll_sec2_comp)

        # Bottom Bar Compromise Section 2
        sec2_comp_bottom = QHBoxLayout()
        btn_c2_back = QPushButton("ย้อนกลับ: ข้อมูลคดี & องค์คณะ")
        btn_c2_back.setObjectName("secondaryButton")
        btn_c2_back.setIcon(get_icon("arrow-left", color="#4c1d95", size=16))
        btn_c2_back.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 9px 16px; font-weight: 500; font-size: 14px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_c2_back.clicked.connect(lambda: self.set_form_section(0))
        sec2_comp_bottom.addWidget(btn_c2_back)
        sec2_comp_bottom.addStretch()

        btn_c2_next = QPushButton("ต่อไป: สรุป & สร้างคำพิพากษาตามยอม")
        btn_c2_next.setObjectName("primaryButtonLarge")
        btn_c2_next.setIcon(get_icon("arrow-right", color="#ffffff", size=16))
        btn_c2_next.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; padding: 13px 30px; font-size: 16px; font-weight: 600; border-radius: 8px; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; } "
            "QPushButton:pressed { background-color: #3b0764; }"
        )
        btn_c2_next.clicked.connect(lambda: self.set_form_section(2))
        sec2_comp_bottom.addWidget(btn_c2_next)
        sec2_comp_vbox.addLayout(sec2_comp_bottom)

        self.form_sub_stack.addWidget(self.page_sec2_compromise)

        # =============================================================
        # SUB-PAGE 4 (Compromise Section 3: สรุปและสร้างเอกสารคำพิพากษาตามยอม)
        # =============================================================
        self.page_sec3_compromise = QWidget()
        sec3_comp_vbox = QVBoxLayout(self.page_sec3_compromise)
        sec3_comp_vbox.setContentsMargins(0, 0, 0, 0)
        sec3_comp_vbox.setSpacing(12)

        scroll_sec3_comp = QScrollArea()
        scroll_sec3_comp.setWidgetResizable(True)
        scroll_sec3_comp.setObjectName("scrollArea")
        container_sec3_comp = QWidget()
        lay_sec3_comp = QVBoxLayout(container_sec3_comp)
        lay_sec3_comp.setContentsMargins(18, 16, 18, 16)
        lay_sec3_comp.setSpacing(14)

        # Dynamic Variables Panel for Compromise (headless/hidden to avoid redundant top panel)
        self.dynamic_variables_panel_comp = DynamicVariablesPanel(self)
        self.dynamic_variables_panel_comp.setVisible(False)
        self.dynamic_variables_panel_comp.btn_apply.clicked.connect(self.apply_dynamic_values_to_paragraph_cards)
        self.dynamic_variables_panel_comp.variable_changed.connect(self._sync_var_to_cards)

        # 1. Summary Card for Compromise (moved from Section 2 to Section 3)
        lay_sec3_comp.addWidget(self.compromise_widget.summary_card)

        # 2. Notice Card for Compromise
        comp_notice_frame = QFrame()
        comp_notice_frame.setObjectName("innerGroupFrame")
        comp_notice_frame.setStyleSheet("background-color: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px;")
        not_lay = QVBoxLayout(comp_notice_frame)
        not_lay.setContentsMargins(18, 16, 18, 16)
        not_lay.setSpacing(8)

        lbl_not_title = QLabel("พร้อมสร้างเอกสารคำพิพากษาตามยอม")
        lbl_not_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #166534;")
        not_lay.addWidget(lbl_not_title)

        lbl_not_desc = QLabel(
            "ระบบได้รวมข้อมูลหมายเลขคดี ศาล คู่ความ สัญญาประนีประนอมยอมความ และยอดเงินคืนค่าขึ้นศาลเรียบร้อยแล้ว\n"
            "ท่านสามารถกดปุ่ม \"สร้างคำพิพากษาตามยอม (.docx)\" ด้านล่างนี้เพื่อสร้างไฟล์ Word ได้ทันที"
        )
        lbl_not_desc.setStyleSheet("font-size: 13.5px; color: #15803d; line-height: 1.5;")
        not_lay.addWidget(lbl_not_desc)
        lay_sec3_comp.addWidget(comp_notice_frame)
        lay_sec3_comp.addStretch()

        scroll_sec3_comp.setWidget(container_sec3_comp)
        sec3_comp_vbox.addWidget(scroll_sec3_comp)

        # Bottom Bar Compromise Section 3
        sec3_comp_bottom = QHBoxLayout()
        btn_c3_back = QPushButton("ย้อนกลับ: ข้อมูลคำพิพากษาตามยอม")
        btn_c3_back.setObjectName("secondaryButton")
        btn_c3_back.setIcon(get_icon("arrow-left", color="#4c1d95", size=16))
        btn_c3_back.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 9px 16px; font-weight: 500; font-size: 14px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_c3_back.clicked.connect(lambda: self.set_form_section(1))
        sec3_comp_bottom.addWidget(btn_c3_back)
        sec3_comp_bottom.addStretch()

        self.btn_generate_compromise = QPushButton("สร้างคำพิพากษาตามยอม (.docx)")
        self.btn_generate_compromise.setObjectName("generateButton")
        self.btn_generate_compromise.setIcon(get_icon("file-text", color="#ffffff", size=18))
        self.btn_generate_compromise.setStyleSheet(
            "QPushButton { background-color: #16a34a; color: #ffffff; padding: 11px 26px; font-size: 15px; font-weight: 600; border-radius: 6px; border: 1px solid #15803d; } "
            "QPushButton:hover { background-color: #15803d; } "
            "QPushButton:pressed { background-color: #166534; }"
        )
        self.btn_generate_compromise.clicked.connect(self.handle_generate_compromise_docx)
        sec3_comp_bottom.addWidget(self.btn_generate_compromise)
        sec3_comp_vbox.addLayout(sec3_comp_bottom)

        self.form_sub_stack.addWidget(self.page_sec3_compromise)

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

        self.txt_compromise_subject = self.compromise_widget.txt_compromise_subject
        self.txt_compromise_date = self.compromise_widget.txt_compromise_date
        self.txt_refund_total = self.compromise_widget.txt_refund_total
        self.lbl_comp_summary_text = self.compromise_widget.lbl_comp_summary_text

        self.group_dyn_fields = self.dynamic_variables_panel
        self.group_dyn_fields_comp = self.dynamic_variables_panel_comp

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
        if self.doc_type == "compromise":
            return self.dynamic_variables_panel_comp.dynamic_inputs
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
        if hasattr(self, 'txt_compromise_subject') and hasattr(self.txt_compromise_subject, 'hide_popup'):
            self.txt_compromise_subject.hide_popup()

    def set_doc_type(self, doc_type: str):
        self.doc_type = doc_type
        if doc_type == "compromise":
            self.lbl_page_title.setText("ขั้นตอนที่ 4: จัดทำคำพิพากษาตามยอม (สัญญาประนีประนอมยอมความ)")
            self.btn_sec_tab1.setText("1. ข้อมูลคดี & องค์คณะ")
            self.btn_sec_tab2.setText("2. ข้อมูลคำพิพากษาตามยอม")
            self.btn_sec_tab2.setIcon(get_icon("scale", color="#4c1d95", size=16))
            self.btn_sec_tab3.setText("3. สรุป & สร้างคำพิพากษาตามยอม")
            self.btn_sec_tab3.setIcon(get_icon("check", color="#4c1d95", size=16))
            self.btn_sec1_next.setText("ต่อไป: ข้อมูลคำพิพากษาตามยอม")
            self.btn_sec1_next.setToolTip("ไปยังขั้นตอนกรอกข้อมูลคำพิพากษาตามยอม [PgDown]")
        else:
            self.lbl_page_title.setText("ขั้นตอนที่ 4: จัดทำรายงานกระบวนพิจารณาคดี")
            self.btn_sec_tab1.setText("1. ข้อมูลคดี & องค์คณะ")
            self.btn_sec_tab2.setText("2. รายชื่อผู้มาศาล")
            self.btn_sec_tab2.setIcon(get_icon("users", color="#4c1d95", size=16))
            self.btn_sec_tab3.setText("3. ย่อหน้ากระบวนพิจารณา & สร้างรายงาน")
            self.btn_sec_tab3.setIcon(get_icon("scale", color="#4c1d95", size=16))
            self.btn_sec1_next.setText("ต่อไป: เลือกรายชื่อผู้มาศาล")
            self.btn_sec1_next.setToolTip("ไปยังขั้นตอนเลือกรายชื่อผู้มาศาล [PgDown]")

        if not self.txt_court_name.text().strip():
            self.refresh_default_court()
        if self.isVisible():
            self.set_form_section(self.form_section)

    def set_form_section(self, idx: int):
        self.form_section = idx
        if hasattr(self, 'form_sub_stack'):
            if self.doc_type == 'compromise':
                if idx == 0:
                    self.form_sub_stack.setCurrentWidget(self.page_sec1)
                elif idx == 1:
                    self.form_sub_stack.setCurrentWidget(self.page_sec2_compromise)
                elif idx == 2:
                    self.update_compromise_summary()
                    self.scan_and_update_dynamic_fields()
                    self.form_sub_stack.setCurrentWidget(self.page_sec3_compromise)
            else:
                if idx == 0:
                    self.form_sub_stack.setCurrentWidget(self.page_sec1)
                elif idx == 1:
                    self.form_sub_stack.setCurrentWidget(self.page_sec2)
                elif idx == 2:
                    self.scan_and_update_dynamic_fields()
                    self.form_sub_stack.setCurrentWidget(self.page_sec3)

        for i, btn in enumerate([self.btn_sec_tab1, self.btn_sec_tab2, self.btn_sec_tab3]):
            btn.setProperty("active", i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.focus_first_field()

    def focus_first_field(self):
        """Smart focus: automatically focus the most appropriate field depending on section."""
        if not self.isVisible():
            return
        if self.form_section == 0:
            self.case_info_widget.focus_first_empty_field()
        elif self.form_section == 1:
            if self.doc_type == 'compromise':
                if not self.txt_compromise_subject.text().strip():
                    self.txt_compromise_subject.setFocus()
                elif not self.txt_compromise_date.text().strip():
                    self.txt_compromise_date.setFocus()
                elif not self.txt_refund_total.text().strip():
                    self.txt_refund_total.setFocus()
            else:
                self.signatories_widget.setFocus()
        elif self.form_section == 2:
            if self.doc_type == 'compromise':
                self.btn_generate_compromise.setFocus()
            else:
                if self.paragraph_cards:
                    card0 = self.paragraph_cards[0]
                    if hasattr(card0, 'txt_editor'):
                        card0.txt_editor.setFocus()
                    elif hasattr(card0, 'txt_content'):
                        card0.txt_content.setFocus()
                else:
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
        d, m, y = self.case_info_widget.load_case_row(row, mapping)
        self.bench_widget.load_bench_data(row, mapping)
        if hasattr(self, 'compromise_widget'):
            self.compromise_widget.load_compromise_data(row, mapping, d, m, y)

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

    def fill_compromise_date_from_excel(self):
        self.compromise_widget.fill_compromise_date_from_values(
            self.txt_day.text().strip(),
            self.txt_month.text().strip(),
            self.txt_year.text().strip()
        )

    def fill_compromise_date_today(self):
        self.compromise_widget.fill_compromise_date_today()

    @staticmethod
    def format_thai_currency(text: str) -> str:
        return CompromiseDetailsWidget.format_thai_currency(text)

    def handle_refund_total_edited(self, raw_text: str):
        self.compromise_widget.handle_refund_total_edited(raw_text)

    def convert_refund_to_thai_digits(self):
        self.compromise_widget.convert_refund_to_thai_digits()

    def update_compromise_summary(self):
        case_data = self.case_info_widget.get_case_data()
        j1, j2 = self.bench_widget.get_judges()
        self.compromise_widget.update_summary(case_data, j1, j2)

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

        is_compromise = (self.doc_type == 'compromise')
        if is_compromise:
            candidates = ["คำพิพากษาตามยอม.docx", "template2.docx"]
            for c in candidates:
                p = os.path.join(tpl_dir, c)
                if os.path.exists(p):
                    return p
            for f in os.listdir(tpl_dir):
                if f.endswith(".docx") and not f.startswith("~$"):
                    if "ตามยอม" in f or "ประนีประนอม" in f or "template2" in f:
                        return os.path.join(tpl_dir, f)
        else:
            # รายงานปกติ: ต้องใช้ไฟล์ รายงานกระบวนพิจารณา.docx เท่านั้น (ห้ามหยิบไฟล์ออนไลน์)
            candidates = ["รายงานกระบวนพิจารณา.docx", "template.docx"]
            for c in candidates:
                p = os.path.join(tpl_dir, c)
                if os.path.exists(p):
                    return p
            for f in os.listdir(tpl_dir):
                if f.endswith(".docx") and not f.startswith("~$"):
                    # ข้ามไฟล์ออนไลน์และคำพิพากษาตามยอม
                    if any(kw in f for kw in ["ออนใลน์", "ออนไลน์", "online", "ตามยอม", "ประนีประนอม"]):
                        continue
                    if "รายงาน" in f or "กระบวน" in f or "template" in f:
                        return os.path.join(tpl_dir, f)
        return None

    def scan_and_update_dynamic_fields(self):
        if self.doc_type == "compromise":
            return
        tpl_path = self.get_active_template_path()
        self.dynamic_variables_panel.scan_and_update(self.paragraph_cards, self.doc_type, tpl_path)
        self.dynamic_variables_panel.setVisible(False)
        self.dynamic_variables_panel_comp.setVisible(False)

    def apply_dynamic_values_to_paragraph_cards(self):
        panel = self.dynamic_variables_panel_comp if self.doc_type == "compromise" else self.dynamic_variables_panel
        panel.apply_dynamic_values_to_paragraph_cards(self.paragraph_cards)
        self.scan_and_update_dynamic_fields()

    def _sync_var_to_cards(self, var_name: str, new_val: str):
        for card in self.paragraph_cards:
            if hasattr(card, 'chip_components') and var_name in card.chip_components:
                comp = card.chip_components[var_name]
                if comp.get_value() != new_val:
                    comp.set_value(new_val)

    def _sync_var_from_card(self, var_name: str, new_val: str):
        panel = self.dynamic_variables_panel_comp if self.doc_type == "compromise" else self.dynamic_variables_panel
        panel.sync_var_from_card(var_name, new_val)

    # -------------------------------------------------------------------------
    # Word Document Generation
    # -------------------------------------------------------------------------
    def trigger_generate_document(self):
        if self.doc_type == 'compromise':
            self.handle_generate_compromise_docx()
        else:
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
                f"ไม่พบไฟล์ Template Word สำหรับรายงานกระบวนพิจารณา (.docx) ในโฟลเดอร์:\n{tpl_dir}\n\nต้องการไฟล์: 'รายงานกระบวนพิจารณา.docx'"
            )
            return

        from services.template_recovery_service import validate_word_template, restore_word_template
        v_res = validate_word_template(tpl_path, "report")
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
        default_filename = f"รายงาน_{safe_black}.docx"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "บันทึกรายงานกระบวนพิจารณา (.docx)", default_filename, "Word Document (*.docx)"
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

        signatories = self.signatories_widget.get_signatories()

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
            'signatories': [{'position': pos} for pos in signatories],
            'attendees_summary': format_attendees_summary(signatories),
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
                generate_report_docx(tpl_path, save_path, data)
            finally:
                while QApplication.overrideCursor():
                    QApplication.restoreOverrideCursor()

            reply = QMessageBox.information(
                self, "สร้างเอกสารสำเร็จ",
                f"สร้างรายงานกระบวนพิจารณาเรียบร้อยแล้ว:\n{save_path}\n\nท่านต้องการเปิดโฟลเดอร์ที่เก็บไฟล์หรือไม่?",
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

    def handle_generate_compromise_docx(self):
        case_black = self.txt_case_black.text().strip()
        if not case_black:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุคดีหมายเลขดำที่ในแบบฟอร์ม")
            self.set_form_section(0)
            self.txt_case_black.setFocus()
            return

        subject = self.txt_compromise_subject.text().strip()
        if not subject:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุ 'เรื่อง (ข้อหาแห่งคดี)' ซึ่งจำเป็นต้องใช้ในคำพิพากษาตามยอม")
            self.set_form_section(1)
            self.txt_compromise_subject.setFocus()
            return

        c_date = self.txt_compromise_date.text().strip()
        if not c_date:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุ 'ฉบับลงวันที่ (สัญญาประนีประนอมยอมความ)' ซึ่งจำเป็นต้องใช้ในคำพิพากษาตามยอม")
            self.set_form_section(1)
            self.txt_compromise_date.setFocus()
            return

        refund = self.txt_refund_total.text().strip()
        if not refund:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุ 'คืนค่าขึ้นศาลเป็นกรณีพิเศษ (บาท)' ซึ่งจำเป็นต้องใช้ในคำพิพากษาตามยอม")
            self.set_form_section(1)
            self.txt_refund_total.setFocus()
            return

        refund = self.format_thai_currency(refund) or refund
        self.txt_refund_total.setText(refund)

        tpl_dir = storage_service.get_templates_dir()
        tpl_candidates = ["คำพิพากษาตามยอม.docx", "template2.docx"]
        tpl_path = None
        for c in tpl_candidates:
            p = os.path.join(tpl_dir, c)
            if os.path.exists(p):
                tpl_path = p
                break

        if not tpl_path and os.path.exists(tpl_dir):
            for f in os.listdir(tpl_dir):
                if f.endswith(".docx") and not f.startswith("~$") and ("ตามยอม" in f or "template2" in f):
                    tpl_path = os.path.join(tpl_dir, f)
                    break

        if not tpl_path or not os.path.exists(tpl_path):
            QMessageBox.critical(
                self, "ข้อผิดพลาด",
                f"ไม่พบไฟล์แม่แบบ Word 'คำพิพากษาตามยอม.docx' ในโฟลเดอร์:\n{tpl_dir}\n\nกรุณาวางไฟล์แม่แบบไว้ที่โฟลเดอร์ templates/"
            )
            return

        from services.template_recovery_service import validate_word_template, restore_word_template
        v_res = validate_word_template(tpl_path, "compromise")
        if not v_res["valid"] and v_res.get("status_level") == "error":
            missing_items = []
            for mr in v_res.get("missing_required", []):
                missing_items.append(f"• {mr['tag']} ({mr['description']})")
            for se in v_res.get("syntax_errors", []):
                missing_items.append(f"• {se}")
            missing_text = "\n".join(missing_items) if missing_items else v_res["status_message"]

            reply = QMessageBox.warning(
                self, "แม่แบบเอกสารไม่สมบูรณ์",
                f"ไฟล์แม่แบบ '{v_res['filename']}' ตรวจพบข้อผิดพลาดที่ไม่สามารถสร้างคำพิพากษาตามยอมได้:\n\n"
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
                else:
                    QMessageBox.critical(self, "กู้คืนล้มเหลว", msg)
                    return
            else:
                return

        safe_black = re.sub(r'[\\/*?:"<>|]', '-', case_black)
        default_filename = f"คำพิพากษาตามยอม_{safe_black}.docx"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "บันทึกคำพิพากษาตามยอม (.docx)", default_filename, "Word Document (*.docx)"
        )
        if not save_path:
            return

        d_val = self.txt_day.text().strip()
        thai_digits = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")
        d_th = d_val.translate(thai_digits) if d_val else ""

        court_val = self.txt_court_name.text().strip() or storage_service.get_default_court_name()
        if not self.txt_court_name.text().strip() and court_val:
            self.txt_court_name.setText(court_val)

        data = {
            'case_black_no': case_black,
            'case_red_no': self.txt_case_red.text().strip(),
            'd': d_th or d_val,
            'day': d_th or d_val,
            'date': d_th or d_val,
            'month': self.txt_month.text().strip(),
            'year': to_full_buddhist_year(self.txt_year.text().strip()) if self.txt_year.text().strip() else "",
            'court_name': court_val,
            'case_type': self.txt_case_type.text().strip(),
            'case_subject': subject,
            'plaintiff_name': self.txt_plaintiff.text().strip(),
            'defendant_name': self.txt_defendant.text().strip(),
            'full_date': c_date,
            'refund_total': refund,
            'judge_1_name': self.txt_judge1.text().strip(),
            'judge_2_name': self.txt_judge2.text().strip(),
        }

        dyn_replacements = self.dynamic_variables_panel_comp.get_dynamic_values()
        for var_name, val in dyn_replacements.items():
            if val:
                data[var_name] = val
                data[parse_variable_tag(var_name)['name']] = val

        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                generate_compromise_docx(tpl_path, save_path, data)
            finally:
                while QApplication.overrideCursor():
                    QApplication.restoreOverrideCursor()

            reply = QMessageBox.information(
                self, "สร้างเอกสารสำเร็จ",
                f"สร้างคำพิพากษาตามยอมเรียบร้อยแล้ว:\n{save_path}\n\nท่านต้องการเปิดโฟลเดอร์ที่เก็บไฟล์หรือไม่?",
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
            QMessageBox.critical(self, "เกิดข้อผิดพลาด", f"ไม่สามารถสร้างเอกสารคำพิพากษาตามยอมได้:\n{str(e)}")

    def get_tutorial_steps(self):
        """Return tutorial steps for Step 4 (Form Page)."""
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
                title="แท็บที่ 2: รายชื่อผู้มาศาล (Attendees)",
                description="สำหรับเลือกชิปตำแหน่งผู้มาศาล เช่น โจทก์ จำเลย ทนายความ พร้อมปุ่มจัดเรียงตามแบบพิธีการศาลไทยอัตโนมัติ",
                preferred_position="bottom"
            ),
            TutorialStep(
                target=self.btn_sec_tab3,
                title="แท็บที่ 3: ข้อความย่อหน้า & ออกเอกสาร",
                description="สำหรับพิมพ์หรือดึงข้อความจากแม่แบบ และกดสร้างไฟล์ Word (.docx) ฉบับสมบูรณ์ (หรือกดคีย์ลัด Ctrl+S)",
                preferred_position="bottom"
            )
        ]

    def has_unsaved_content(self) -> bool:
        """Check if user has modified form data or added non-empty paragraphs."""
        for card in self.paragraph_cards:
            if hasattr(card, 'get_text') and card.get_text().strip():
                return True
        if hasattr(self, 'txt_case_black') and self.txt_case_black.text().strip():
            return True
        return False

    def handle_check_or_recover_template(self, tpl_key: str = "report"):
        from ui.dialogs.template_recovery_dialog import TemplateRecoveryDialog
        dlg = TemplateRecoveryDialog(self, initial_tpl_key=tpl_key)
        dlg.exec()
        self.scan_and_update_dynamic_fields()
