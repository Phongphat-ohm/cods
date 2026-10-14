"""
Page 3: 3-Section Sequential Wizard Workflow
Section 1: Case Information & Bench Judges Pairing
Section 2: Signatories / Attendees Ordering
Section 3: Optional Paragraphs & Word Document Generator
"""

import os
import re
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QMessageBox, QComboBox,
    QCompleter, QStackedWidget, QFileDialog, QSizePolicy,
    QApplication
)
from PySide6.QtCore import Qt, Signal, QStringListModel, QRegularExpression
from PySide6.QtGui import QIntValidator, QRegularExpressionValidator

from constants import DEFAULT_CASE_TYPES
from excel_service import format_thai_date, to_full_buddhist_year, THAI_MONTHS
from docx_service import (
    generate_report_docx,
    generate_compromise_docx,
    format_attendees_summary,
    extract_and_categorize_template_variables,
    FORBIDDEN_CONTROL_KEYWORDS,
    SYSTEM_RESERVED_VARIABLES,
    validate_template_variable
)
import storage_service
from dialogs import TemplateSelectDialog, BenchManagerDialog
from ui_components import ParagraphCard, SignatoriesManagerWidget, JudicialAccentCard
from ui.components.autocomplete_input import JudicialAutocompleteInput
from icon_service import get_icon, get_pixmap

COMMON_HEARING_PURPOSES = [
    "ชี้สองสถาน", "นัดพร้อม", "สืบพยานโจทก์", "สืบพยานจำเลย",
    "ฟังคำพิพากษา", "ฟังคำสั่ง", "ไกล่เกลี่ย", "ตรวจพยานหลักฐาน",
    "สอบคำให้การ", "สืบพยานโจทก์นัดแรก", "นัดกำหนดวันสืบพยาน"
]

COMMON_COURTS = [
    "ศาลแพ่ง", "ศาลแพ่งกรุงเทพใต้", "ศาลแพ่งธนบุรี", "ศาลอาญา",
    "ศาลจังหวัดนนทบุรี", "ศาลจังหวัดนางรอง", "ศาลจังหวัดเชียงใหม่",
    "ศาลแขวงดอนเมือง", "ศาลแขวงพระนครเหนือ", "ศาลแขวงพระนครใต้"
]


class FormPage(QWidget):
    """Step 3: Comprehensive 3-section form for case details, attendees, and document generation."""

    back_to_doc_type_requested = Signal()
    back_to_table_requested = Signal()
    bench_manager_requested = Signal()
    court_saved_as_default = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc_type: str = "report"
        self.form_section = 0
        self.paragraph_cards: List[ParagraphCard] = []
        self.case_types_list: List[str] = list(DEFAULT_CASE_TYPES)
        self.dynamic_inputs: Dict[str, QLineEdit] = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 20, 32, 20)
        layout.setSpacing(14)

        # Header Bar
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
        # Sub Stacked Widget (3 Distinct Sequential Sections)
        # -------------------------------------------------------------
        self.form_sub_stack = QStackedWidget()
        self.form_sub_stack.setObjectName("formSubStack")

        # =============================================================
        # SUB-PAGE 0 (Section 1: ข้อมูลคดีความและองค์คณะ)
        # =============================================================
        page_sec1 = QWidget()
        sec1_vbox = QVBoxLayout(page_sec1)
        sec1_vbox.setContentsMargins(0, 0, 0, 0)
        sec1_vbox.setSpacing(12)

        scroll_sec1 = QScrollArea()
        scroll_sec1.setWidgetResizable(True)
        scroll_sec1.setObjectName("scrollArea")
        container_sec1 = QWidget()
        lay_sec1 = QVBoxLayout(container_sec1)
        lay_sec1.setContentsMargins(18, 16, 18, 16)
        lay_sec1.setSpacing(18)

        # Frame 1: ข้อมูลคดี
        group_case = QFrame()
        group_case.setObjectName("innerGroupFrame")
        group_case_layout = QVBoxLayout(group_case)
        group_case_layout.setContentsMargins(20, 18, 20, 20)
        group_case_layout.setSpacing(14)

        lbl_sec1 = QLabel("ข้อมูลคดีความและรายละเอียดนัดพิจารณา")
        lbl_sec1.setObjectName("sectionHeaderTitle")
        group_case_layout.addWidget(lbl_sec1)

        row1 = QHBoxLayout()
        row1.setSpacing(14)
        self.txt_case_black = self.create_form_field(row1, "คดีหมายเลขดำที่", "")
        self.txt_case_red = self.create_form_field(row1, "คดีหมายเลขแดงที่", "")

        # Court field with default save button
        v_court = QVBoxLayout()
        v_court.setSpacing(5)
        h_court_head = QHBoxLayout()
        lbl_court = QLabel("ศาล")
        lbl_court.setObjectName("fieldLabel")
        h_court_head.addWidget(lbl_court)
        h_court_head.addStretch()

        btn_save_court = QPushButton("ตั้งเป็นศาลเริ่มต้น")
        btn_save_court.setObjectName("secondaryButtonSmall")
        btn_save_court.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        btn_save_court.setIcon(get_icon("save", color="#4c1d95", size=14))
        btn_save_court.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1px solid #d8b4fe; border-radius: 5px; padding: 4px 10px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #e9d5ff; border-color: #c084fc; }"
        )
        btn_save_court.setToolTip("บันทึกชื่อศาลนี้เป็นค่าเริ่มต้น เพื่อให้ระบบนำมาแสดงให้อัตโนมัติในทุกคดี")
        btn_save_court.clicked.connect(self.save_current_court_as_default)
        h_court_head.addWidget(btn_save_court)
        v_court.addLayout(h_court_head)

        self.txt_court_name = JudicialAutocompleteInput(items=COMMON_COURTS, placeholder="พิมพ์หรือเลือกชื่อศาล...")
        self.txt_court_name.setText(storage_service.get_default_court_name())
        v_court.addWidget(self.txt_court_name)
        row1.addLayout(v_court)
        group_case_layout.addLayout(row1)

        row_extra = QHBoxLayout()
        row_extra.setSpacing(14)
        self.txt_case_type = JudicialAutocompleteInput(items=self.case_types_list, placeholder="พิมพ์หรือเลือกประเภทคดี...")
        self.create_form_field(row_extra, "ประเภทคดี (ความ)", "", widget=self.txt_case_type)

        self.txt_hearing_purpose = JudicialAutocompleteInput(items=COMMON_HEARING_PURPOSES, placeholder="พิมพ์หรือเลือกเหตุที่นัด...")
        self.create_form_field(row_extra, "เหตุที่นัด", "", widget=self.txt_hearing_purpose)
        group_case_layout.addLayout(row_extra)

        row2 = QHBoxLayout()
        row2.setSpacing(14)
        self.txt_day = self.create_form_field(row2, "วันที่", "")
        self.txt_day.setValidator(QIntValidator(1, 31, self))
        self.txt_month = JudicialAutocompleteInput(items=THAI_MONTHS, placeholder="พิมพ์หรือเลือกเดือน...")
        self.create_form_field(row2, "เดือน", "", widget=self.txt_month)

        self.txt_year = self.create_form_field(row2, "พ.ศ.", "")
        self.txt_year.setValidator(QIntValidator(1, 9999, self))
        self.txt_time = self.create_form_field(row2, "เวลานัด", "")
        group_case_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.setSpacing(14)
        self.txt_plaintiff = self.create_form_field(row3, "โจทก์ / ผู้ร้อง", "")
        self.txt_defendant = self.create_form_field(row3, "จำเลย / ผู้คัดค้าน", "")
        group_case_layout.addLayout(row3)

        # Bench / Judges Row
        bench_frame = JudicialAccentCard(
            stripe_color="#4c1d95",
            border_color="#d8b4fe",
            bg_color="#faf5ff",
            stripe_width=5,
            radius=8
        )
        bench_frame.setObjectName("benchContainer")
        bench_layout = QVBoxLayout(bench_frame)
        bench_layout.setContentsMargins(18, 14, 16, 16)
        bench_layout.setSpacing(10)

        bench_header_bar = QHBoxLayout()
        lbl_bench_title = QLabel("องค์คณะผู้พิพากษา (เลือกผู้พิพากษาเจ้าของสำนวน แล้วองค์คณะจะแสดงอัตโนมัติตามที่จับคู่ไว้)")
        lbl_bench_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #4c1d95;")
        bench_header_bar.addWidget(lbl_bench_title)
        bench_header_bar.addStretch()

        btn_save_pairing = QPushButton("บันทึกการจับคู่นี้ (สำหรับครั้งต่อไป)")
        btn_save_pairing.setObjectName("secondaryButtonSmall")
        btn_save_pairing.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        btn_save_pairing.setIcon(get_icon("link", color="#4c1d95", size=14))
        btn_save_pairing.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1px solid #d8b4fe; border-radius: 5px; padding: 4px 10px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #e9d5ff; border-color: #c084fc; }"
        )
        btn_save_pairing.setToolTip("บันทึกการจับคู่ระหว่างผู้พิพากษาเจ้าของสำนวนและองค์คณะไว้ในระบบ")
        btn_save_pairing.clicked.connect(self.handle_save_current_pairing)
        bench_header_bar.addWidget(btn_save_pairing)

        btn_bench_config = QPushButton("จัดการคู่องค์คณะ...")
        btn_bench_config.setObjectName("secondaryButtonSmall")
        btn_bench_config.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        btn_bench_config.setIcon(get_icon("settings", color="#4c1d95", size=14))
        btn_bench_config.setStyleSheet(
            "QPushButton { background-color: #ffffff; color: #4c1d95; border: 1.5px solid #d8b4fe; border-radius: 5px; padding: 4px 10px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; }"
        )
        btn_bench_config.setToolTip("จัดการคู่องค์คณะผู้พิพากษา [Ctrl+B]")
        btn_bench_config.clicked.connect(self.bench_manager_requested.emit)
        bench_header_bar.addWidget(btn_bench_config)

        bench_layout.addLayout(bench_header_bar)

        row4 = QHBoxLayout()
        row4.setSpacing(14)

        # Judge 1 Autocomplete Input
        v_j1 = QVBoxLayout()
        v_j1.setSpacing(5)
        lbl_j1 = QLabel("ผู้พิพากษาเจ้าของสำนวน")
        lbl_j1.setObjectName("fieldLabel")
        self.txt_judge1 = JudicialAutocompleteInput(items=[], placeholder="พิมพ์หรือเลือกชื่อผู้พิพากษาเจ้าของสำนวน...")
        self.txt_judge1.textChanged.connect(self.handle_judge1_changed)
        v_j1.addWidget(lbl_j1)
        v_j1.addWidget(self.txt_judge1)
        row4.addLayout(v_j1)

        # Judge 2 Autocomplete Input
        v_j2 = QVBoxLayout()
        v_j2.setSpacing(5)
        lbl_j2 = QLabel("ผู้พิพากษาองค์คณะ")
        lbl_j2.setObjectName("fieldLabel")
        self.txt_judge2 = JudicialAutocompleteInput(items=[], placeholder="ชื่อผู้พิพากษาองค์คณะ (ขึ้นอัตโนมัติหรือเลือกได้)...")
        v_j2.addWidget(lbl_j2)
        v_j2.addWidget(self.txt_judge2)
        row4.addLayout(v_j2)

        bench_layout.addLayout(row4)

        self.lbl_bench_status = QLabel("")
        self.lbl_bench_status.setStyleSheet("font-size: 13px; color: #0284c7; font-weight: 500;")
        self.lbl_bench_status.setVisible(False)
        bench_layout.addWidget(self.lbl_bench_status)

        group_case_layout.addWidget(bench_frame)
        lay_sec1.addWidget(group_case)
        lay_sec1.addStretch()

        scroll_sec1.setWidget(container_sec1)
        sec1_vbox.addWidget(scroll_sec1)

        # Bottom bar Section 1
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

        self.page_sec1 = page_sec1
        self.form_sub_stack.addWidget(page_sec1)

        # =============================================================
        # SUB-PAGE 1 (Section 2: เลือกรายชื่อผู้มาศาล)
        # =============================================================
        page_sec2 = QWidget()
        sec2_vbox = QVBoxLayout(page_sec2)
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

        # Bottom bar Section 2
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

        self.page_sec2 = page_sec2
        self.form_sub_stack.addWidget(page_sec2)

        # =============================================================
        # SUB-PAGE 2 (Section 3: ย่อหน้ากระบวนพิจารณา & สร้างรายงาน Word)
        # Starts with 0 paragraph cards!
        # =============================================================
        page_sec3 = QWidget()
        sec3_vbox = QVBoxLayout(page_sec3)
        sec3_vbox.setContentsMargins(0, 0, 0, 0)
        sec3_vbox.setSpacing(12)

        scroll_sec3 = QScrollArea()
        scroll_sec3.setWidgetResizable(True)
        scroll_sec3.setObjectName("scrollArea")
        container_sec3 = QWidget()
        lay_sec3 = QVBoxLayout(container_sec3)
        lay_sec3.setContentsMargins(18, 16, 18, 16)
        lay_sec3.setSpacing(14)

        # Dynamic Template Variables Container
        self.group_dyn_fields, self.dyn_inputs_container = self._create_dynamic_fields_widget()
        lay_sec3.addWidget(self.group_dyn_fields)

        group_para = QFrame()
        group_para.setObjectName("innerGroupFrame")
        self.group_para_layout = QVBoxLayout(group_para)
        self.group_para_layout.setContentsMargins(20, 18, 20, 20)
        self.group_para_layout.setSpacing(14)

        # Paragraphs Header Toolbar
        para_top_bar = QHBoxLayout()
        v_para_title = QVBoxLayout()
        v_para_title.setSpacing(3)
        lbl_sec3 = QLabel("3. เนื้อหาข้อความกระบวนพิจารณาเพิ่มเติม (ไม่จำเป็นต้องมี)")
        lbl_sec3.setObjectName("sectionHeaderTitle")
        self.lbl_para_count = QLabel("(เริ่มต้นไม่มีกล่องข้อความ - กดปุ่มด้านขวาเพื่อเพิ่มหากต้องการ)")
        self.lbl_para_count.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 500;")
        v_para_title.addWidget(lbl_sec3)
        v_para_title.addWidget(self.lbl_para_count)
        para_top_bar.addLayout(v_para_title)
        para_top_bar.addStretch()

        btn_add_from_tpl = QPushButton("เพิ่มย่อหน้าจาก Template")
        btn_add_from_tpl.setObjectName("secondaryButtonSmall")
        btn_add_from_tpl.setStyleSheet("""
            QPushButton {
                background-color: #f3e8ff;
                color: #4c1d95;
                border: 1.5px solid #a855f7;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ede9fe;
                border-color: #7c3aed;
            }
        """)
        btn_add_from_tpl.setIcon(get_icon("clipboard-list", color="#4c1d95", size=15))
        btn_add_from_tpl.setToolTip("เลือกข้อความสำเร็จรูปจาก Template มาสร้างย่อหน้าใหม่ [Ctrl+T]")
        btn_add_from_tpl.clicked.connect(self.handle_add_paragraph_from_template)
        para_top_bar.addWidget(btn_add_from_tpl)

        btn_add_para = QPushButton("เพิ่มย่อหน้าเปล่า")
        btn_add_para.setObjectName("primaryButtonSmall")
        btn_add_para.setIcon(get_icon("plus", color="#ffffff", size=15))
        btn_add_para.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; border-radius: 5px; padding: 6px 14px; font-size: 13px; font-weight: 500; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; }"
        )
        btn_add_para.setToolTip("เพิ่มกล่องข้อความย่อหน้าเปล่าใหม่")
        btn_add_para.clicked.connect(lambda: self.add_paragraph_card())
        para_top_bar.addWidget(btn_add_para)

        self.group_para_layout.addLayout(para_top_bar)

        # Placeholder box when 0 paragraphs exist
        self.para_placeholder = QFrame()
        self.para_placeholder.setObjectName("paraPlaceholderBox")
        place_layout = QVBoxLayout(self.para_placeholder)
        place_layout.setContentsMargins(24, 28, 24, 28)
        place_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_layout.setSpacing(12)

        place_icon = QLabel()
        place_icon.setPixmap(get_pixmap("file-text", color="#94a3b8", size=42))
        place_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_layout.addWidget(place_icon)

        place_lbl_main = QLabel("ยังไม่มีข้อความกระบวนพิจารณาเพิ่มเติม")
        place_lbl_main.setStyleSheet("font-size: 16px; font-weight: 600; color: #334155;")
        place_lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_layout.addWidget(place_lbl_main)

        place_lbl_sub = QLabel(
            "ย่อหน้าเพิ่มเติมเป็นตัวเลือกเสริม ท่านสามารถกดปุ่ม \"สร้างรายงานกระบวนพิจารณา (.docx)\" ได้ทันที\n"
            "หรือกดเลือกข้อความจาก Template หรือพิมพ์ย่อหน้าใหม่ได้ตามปุ่มด้านล่างนี้"
        )
        place_lbl_sub.setStyleSheet("font-size: 14px; color: #64748b; line-height: 1.5;")
        place_lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_layout.addWidget(place_lbl_sub)

        # Prominent Action Buttons in Central Placeholder Box
        place_btn_row = QHBoxLayout()
        place_btn_row.setSpacing(12)
        place_btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_place_add_tpl = QPushButton("เพิ่มย่อหน้าจาก Template")
        btn_place_add_tpl.setObjectName("primaryButton")
        btn_place_add_tpl.setIcon(get_icon("clipboard-list", color="#ffffff", size=16))
        btn_place_add_tpl.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 22px;
                border-radius: 7px;
                border: 1px solid #3b0764;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
        """)
        btn_place_add_tpl.setToolTip("เลือกข้อความสำเร็จรูปจาก Template มาเพิ่มเป็นย่อหน้าแรก [Ctrl+T]")
        btn_place_add_tpl.clicked.connect(self.handle_add_paragraph_from_template)
        place_btn_row.addWidget(btn_place_add_tpl)

        btn_place_add = QPushButton("เพิ่มย่อหน้าข้อความเปล่า")
        btn_place_add.setObjectName("secondaryButton")
        btn_place_add.setIcon(get_icon("plus", color="#4c1d95", size=15))
        btn_place_add.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #d8b4fe;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 7px;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
                border-color: #c084fc;
            }
        """)
        btn_place_add.clicked.connect(lambda: self.add_paragraph_card())
        place_btn_row.addWidget(btn_place_add)

        place_layout.addLayout(place_btn_row)

        self.group_para_layout.addWidget(self.para_placeholder)

        # Container for paragraph cards
        self.para_cards_container = QVBoxLayout()
        self.para_cards_container.setSpacing(14)
        self.group_para_layout.addLayout(self.para_cards_container)

        # Bottom Add Paragraph Buttons (visible only when cards > 0)
        self.bottom_add_container = QHBoxLayout()
        self.bottom_add_container.setSpacing(10)

        self.btn_bottom_add_tpl = QPushButton("เพิ่มย่อหน้าจาก Template")
        self.btn_bottom_add_tpl.setObjectName("secondaryButton")
        self.btn_bottom_add_tpl.setIcon(get_icon("clipboard-list", color="#4c1d95", size=15))
        self.btn_bottom_add_tpl.setStyleSheet("""
            QPushButton {
                background-color: #f3e8ff;
                color: #4c1d95;
                border: 1.5px solid #a855f7;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ede9fe;
            }
        """)
        self.btn_bottom_add_tpl.clicked.connect(self.handle_add_paragraph_from_template)
        self.btn_bottom_add_tpl.setVisible(False)
        self.bottom_add_container.addWidget(self.btn_bottom_add_tpl)

        self.btn_bottom_add_para = QPushButton("เพิ่มย่อหน้าเปล่าต่อท้าย")
        self.btn_bottom_add_para.setObjectName("secondaryButton")
        self.btn_bottom_add_para.setIcon(get_icon("plus", color="#4c1d95", size=15))
        self.btn_bottom_add_para.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #d8b4fe;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13.5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
            }
        """)
        self.btn_bottom_add_para.clicked.connect(lambda: self.add_paragraph_card())
        self.btn_bottom_add_para.setVisible(False)
        self.bottom_add_container.addWidget(self.btn_bottom_add_para)
        self.bottom_add_container.addStretch()

        self.group_para_layout.addLayout(self.bottom_add_container)

        lay_sec3.addWidget(group_para)
        lay_sec3.addStretch()

        scroll_sec3.setWidget(container_sec3)
        sec3_vbox.addWidget(scroll_sec3)

        # Bottom bar Section 3
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

        self.page_sec3 = page_sec3
        self.form_sub_stack.addWidget(page_sec3)

        # =============================================================
        # SUB-PAGE 3 (Compromise Section 2: ข้อมูลสัญญาประนีประนอมยอมความ)
        # =============================================================
        page_sec2_comp = QWidget()
        sec2_comp_vbox = QVBoxLayout(page_sec2_comp)
        sec2_comp_vbox.setContentsMargins(0, 0, 0, 0)
        sec2_comp_vbox.setSpacing(12)

        scroll_sec2_comp = QScrollArea()
        scroll_sec2_comp.setWidgetResizable(True)
        scroll_sec2_comp.setObjectName("scrollArea")
        container_sec2_comp = QWidget()
        lay_sec2_comp = QVBoxLayout(container_sec2_comp)
        lay_sec2_comp.setContentsMargins(18, 16, 18, 16)
        lay_sec2_comp.setSpacing(18)

        # Frame for required compromise terms
        group_comp = QFrame()
        group_comp.setObjectName("innerGroupFrame")
        group_comp_lay = QVBoxLayout(group_comp)
        group_comp_lay.setContentsMargins(20, 18, 20, 20)
        group_comp_lay.setSpacing(14)

        h_comp_title = QHBoxLayout()
        lbl_comp_title = QLabel("รายละเอียดสัญญาประนีประนอมยอมความและคำพิพากษาตามยอม")
        lbl_comp_title.setObjectName("sectionHeaderTitle")
        h_comp_title.addWidget(lbl_comp_title)
        h_comp_title.addStretch()

        badge_req = QLabel("* จำเป็นต้องกรอกทุกช่อง")
        badge_req.setStyleSheet("font-size: 13px; font-weight: 600; color: #dc2626; background: #fee2e2; border-radius: 6px; padding: 4px 10px;")
        h_comp_title.addWidget(badge_req)
        group_comp_lay.addLayout(h_comp_title)

        # Field 1: เรื่อง (case_subject)
        v_subj = QVBoxLayout()
        v_subj.setSpacing(5)
        h_subj_lbl = QHBoxLayout()
        lbl_subj = QLabel("เรื่อง (ข้อหา / ข้อพิพาทแห่งคดี)")
        lbl_subj.setObjectName("fieldLabel")
        lbl_req1 = QLabel("* (จำเป็นต้องกรอก)")
        lbl_req1.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: 600;")
        h_subj_lbl.addWidget(lbl_subj)
        h_subj_lbl.addWidget(lbl_req1)
        h_subj_lbl.addStretch()
        v_subj.addLayout(h_subj_lbl)

        self.txt_compromise_subject = JudicialAutocompleteInput(items=[])
        self.txt_compromise_subject.setPlaceholderText("ข้อหาแห่งคดี (จะดึงจากตาราง Excel อัตโนมัติ หรือพิมพ์แก้ไขได้)")
        v_subj.addWidget(self.txt_compromise_subject)
        group_comp_lay.addLayout(v_subj)

        # Field 2: สัญญาประนีประนอมยอมความ ฉบับลงวันที่ (full_date)
        v_date = QVBoxLayout()
        v_date.setSpacing(5)
        h_date_lbl = QHBoxLayout()
        lbl_date = QLabel("ฉบับลงวันที่ (สัญญาประนีประนอมยอมความ)")
        lbl_date.setObjectName("fieldLabel")
        lbl_req2 = QLabel("* (จำเป็นต้องกรอก)")
        lbl_req2.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: 600;")
        h_date_lbl.addWidget(lbl_date)
        h_date_lbl.addWidget(lbl_req2)
        h_date_lbl.addStretch()
        v_date.addLayout(h_date_lbl)

        h_date_input = QHBoxLayout()
        h_date_input.setSpacing(10)
        self.txt_compromise_date = QLineEdit()
        self.txt_compromise_date.setPlaceholderText("เช่น 17 กันยายน 2569 หรือ ๑๗ กันยายน ๒๕๖๙")
        h_date_input.addWidget(self.txt_compromise_date, 1)

        btn_use_excel = QPushButton("ใช้วันนัดใน Excel")
        btn_use_excel.setObjectName("secondaryButtonSmall")
        btn_use_excel.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        btn_use_excel.setIcon(get_icon("calendar", color="#4c1d95", size=14))
        btn_use_excel.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1px solid #d8b4fe; border-radius: 5px; padding: 5px 12px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #e9d5ff; border-color: #c084fc; }"
        )
        btn_use_excel.setToolTip("นำวัน เดือน ปี จากตาราง Excel มาใส่ในรูปแบบทางการ")
        btn_use_excel.clicked.connect(self.fill_compromise_date_from_excel)
        h_date_input.addWidget(btn_use_excel)

        btn_use_today = QPushButton("ใส่วันนี้")
        btn_use_today.setObjectName("secondaryButtonSmall")
        btn_use_today.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        btn_use_today.setIcon(get_icon("clock", color="#4c1d95", size=14))
        btn_use_today.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1px solid #d8b4fe; border-radius: 5px; padding: 5px 12px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #e9d5ff; border-color: #c084fc; }"
        )
        btn_use_today.setToolTip("ใส่วันที่ปัจจุบันในรูปแบบภาษาไทย")
        btn_use_today.clicked.connect(self.fill_compromise_date_today)
        h_date_input.addWidget(btn_use_today)
        v_date.addLayout(h_date_input)
        group_comp_lay.addLayout(v_date)

        # Field 3: คืนค่าขึ้นศาลเป็นกรณีพิเศษ (refund_total)
        v_refund = QVBoxLayout()
        v_refund.setSpacing(5)
        h_ref_lbl = QHBoxLayout()
        lbl_ref = QLabel("คืนค่าขึ้นศาลแก่โจทก์เป็นกรณีพิเศษ จำนวน (บาท)")
        lbl_ref.setObjectName("fieldLabel")
        lbl_req3 = QLabel("* (จำเป็นต้องกรอก)")
        lbl_req3.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: 600;")
        h_ref_lbl.addWidget(lbl_ref)
        h_ref_lbl.addWidget(lbl_req3)
        h_ref_lbl.addStretch()
        v_refund.addLayout(h_ref_lbl)

        h_ref_input = QHBoxLayout()
        h_ref_input.setSpacing(10)
        self.txt_refund_total = QLineEdit()
        rx_money = QRegularExpression("[0-9๐-๙,.]*")
        self.txt_refund_total.setValidator(QRegularExpressionValidator(rx_money, self))
        self.txt_refund_total.setPlaceholderText("เช่น ๒,๐๐๐ หรือ 2,000")
        self.txt_refund_total.textEdited.connect(self.handle_refund_total_edited)
        h_ref_input.addWidget(self.txt_refund_total, 1)

        btn_to_thai = QPushButton("แปลงเป็นเลขไทย (๑, ๒, ๓...)")
        btn_to_thai.setObjectName("secondaryButtonSmall")
        btn_to_thai.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        btn_to_thai.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1px solid #d8b4fe; border-radius: 5px; padding: 5px 12px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #e9d5ff; border-color: #c084fc; }"
        )
        btn_to_thai.setToolTip("แปลงตัวเลขอารบิกที่พิมพ์ให้เป็นตัวเลขไทย")
        btn_to_thai.clicked.connect(self.convert_refund_to_thai_digits)
        h_ref_input.addWidget(btn_to_thai)
        v_refund.addLayout(h_ref_input)
        group_comp_lay.addLayout(v_refund)

        lay_sec2_comp.addWidget(group_comp)
        lay_sec2_comp.addStretch()
        scroll_sec2_comp.setWidget(container_sec2_comp)
        sec2_comp_vbox.addWidget(scroll_sec2_comp, 1)

        # Bottom navigation
        sec2_comp_bottom = QHBoxLayout()
        btn_comp_b1 = QPushButton("ย้อนกลับ: ข้อมูลคดี & องค์คณะ")
        btn_comp_b1.setObjectName("secondaryButton")
        btn_comp_b1.setIcon(get_icon("arrow-left", color="#4c1d95", size=16))
        btn_comp_b1.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 9px 16px; font-weight: 500; font-size: 14px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_comp_b1.clicked.connect(lambda: self.set_form_section(0))
        sec2_comp_bottom.addWidget(btn_comp_b1)
        sec2_comp_bottom.addStretch()

        btn_comp_n1 = QPushButton("ต่อไป: ตรวจสอบและสร้างคำพิพากษาตามยอม")
        btn_comp_n1.setObjectName("primaryButtonLarge")
        btn_comp_n1.setIcon(get_icon("arrow-right", color="#ffffff", size=16))
        btn_comp_n1.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; padding: 13px 30px; font-size: 16px; font-weight: 600; border-radius: 8px; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; } "
            "QPushButton:pressed { background-color: #3b0764; }"
        )
        btn_comp_n1.clicked.connect(lambda: self.set_form_section(2))
        sec2_comp_bottom.addWidget(btn_comp_n1)
        sec2_comp_vbox.addLayout(sec2_comp_bottom)

        self.page_sec2_compromise = page_sec2_comp
        self.form_sub_stack.addWidget(page_sec2_comp)

        # =============================================================
        # SUB-PAGE 4 (Compromise Section 3: ตรวจสอบและสร้างคำพิพากษาตามยอม)
        # =============================================================
        page_sec3_comp = QWidget()
        sec3_comp_vbox = QVBoxLayout(page_sec3_comp)
        sec3_comp_vbox.setContentsMargins(0, 0, 0, 0)
        sec3_comp_vbox.setSpacing(12)

        scroll_sec3_comp = QScrollArea()
        scroll_sec3_comp.setWidgetResizable(True)
        scroll_sec3_comp.setObjectName("scrollArea")
        container_sec3_comp = QWidget()
        lay_sec3_comp = QVBoxLayout(container_sec3_comp)
        lay_sec3_comp.setContentsMargins(18, 16, 18, 16)
        lay_sec3_comp.setSpacing(18)

        # Dynamic Template Variables Container for Compromise
        self.group_dyn_fields_comp, self.dyn_inputs_container_comp = self._create_dynamic_fields_widget()
        lay_sec3_comp.addWidget(self.group_dyn_fields_comp)

        # Overview Card
        group_sum = QFrame()
        group_sum.setObjectName("innerGroupFrame")
        lay_sum = QVBoxLayout(group_sum)
        lay_sum.setContentsMargins(20, 18, 20, 20)
        lay_sum.setSpacing(14)

        lbl_sum_head = QLabel("ตรวจสอบสรุปข้อมูลก่อนสร้างเอกสารคำพิพากษาตามยอม")
        lbl_sum_head.setObjectName("sectionHeaderTitle")
        lay_sum.addWidget(lbl_sum_head)

        self.lbl_comp_summary_text = QLabel()
        self.lbl_comp_summary_text.setStyleSheet("font-size: 14px; line-height: 1.6; color: #1e293b; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px;")
        self.lbl_comp_summary_text.setWordWrap(True)
        lay_sum.addWidget(self.lbl_comp_summary_text)

        # Template info box
        tpl_info = QLabel("แม่แบบเอกสารที่ใช้: templates/คำพิพากษาตามยอม.docx (แบบพิมพ์ ๓๐)")
        tpl_info.setStyleSheet("font-size: 13px; font-weight: 500; color: #1e3a8a; background: #eff6ff; border-radius: 6px; padding: 8px 12px;")
        lay_sum.addWidget(tpl_info)

        # Big Generate Button
        self.btn_generate_compromise = QPushButton("สร้างคำพิพากษาตามยอม (.docx)")
        self.btn_generate_compromise.setObjectName("primaryButtonLarge")
        self.btn_generate_compromise.setIcon(get_icon("scale", color="#ffffff", size=18))
        self.btn_generate_compromise.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; font-size: 16px; padding: 12px 24px; font-weight: 600; border-radius: 8px; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; } "
            "QPushButton:pressed { background-color: #3b0764; }"
        )
        self.btn_generate_compromise.clicked.connect(self.handle_generate_compromise_docx)
        lay_sum.addWidget(self.btn_generate_compromise)

        lay_sec3_comp.addWidget(group_sum)
        lay_sec3_comp.addStretch()
        scroll_sec3_comp.setWidget(container_sec3_comp)
        sec3_comp_vbox.addWidget(scroll_sec3_comp, 1)

        # Bottom navigation
        sec3_comp_bottom = QHBoxLayout()
        btn_comp_b2 = QPushButton("ย้อนกลับ: ข้อมูลคำพิพากษาตามยอม")
        btn_comp_b2.setObjectName("secondaryButton")
        btn_comp_b2.setIcon(get_icon("arrow-left", color="#4c1d95", size=16))
        btn_comp_b2.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 9px 16px; font-weight: 500; font-size: 14px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_comp_b2.clicked.connect(lambda: self.set_form_section(1))
        sec3_comp_bottom.addWidget(btn_comp_b2)
        sec3_comp_bottom.addStretch()
        sec3_comp_vbox.addLayout(sec3_comp_bottom)

        self.page_sec3_compromise = page_sec3_comp
        self.form_sub_stack.addWidget(page_sec3_comp)

        layout.addWidget(self.form_sub_stack)

        # Tab Navigation Ordering for streamlined keyboard entry
        QWidget.setTabOrder(self.txt_case_black, self.txt_case_red)
        QWidget.setTabOrder(self.txt_case_red, self.txt_court_name)
        QWidget.setTabOrder(self.txt_court_name, self.txt_case_type)
        QWidget.setTabOrder(self.txt_case_type, self.txt_hearing_purpose)
        QWidget.setTabOrder(self.txt_hearing_purpose, self.txt_day)
        QWidget.setTabOrder(self.txt_day, self.txt_month)
        QWidget.setTabOrder(self.txt_month, self.txt_year)
        QWidget.setTabOrder(self.txt_year, self.txt_time)
        QWidget.setTabOrder(self.txt_time, self.txt_plaintiff)
        QWidget.setTabOrder(self.txt_plaintiff, self.txt_defendant)
        QWidget.setTabOrder(self.txt_defendant, self.txt_judge1)
        QWidget.setTabOrder(self.txt_judge1, self.txt_judge2)
        QWidget.setTabOrder(self.txt_judge2, self.btn_sec1_next)

        QWidget.setTabOrder(self.txt_compromise_subject, self.txt_compromise_date)
        QWidget.setTabOrder(self.txt_compromise_date, self.txt_refund_total)
        QWidget.setTabOrder(self.txt_refund_total, btn_comp_n1)

        self.set_form_section(0)
        self.refresh_judge1_completer()

    @property
    def cmb_judge1(self):
        """Compatibility property for legacy references to cmb_judge1."""
        return self.txt_judge1

    def showEvent(self, event):
        super().showEvent(event)
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
            if getattr(self, 'doc_type', 'report') == 'compromise':
                if idx == 0 and hasattr(self, 'page_sec1'):
                    self.form_sub_stack.setCurrentWidget(self.page_sec1)
                elif idx == 1 and hasattr(self, 'page_sec2_compromise'):
                    self.form_sub_stack.setCurrentWidget(self.page_sec2_compromise)
                elif idx == 2 and hasattr(self, 'page_sec3_compromise'):
                    self.update_compromise_summary()
                    self.scan_and_update_dynamic_fields()
                    self.form_sub_stack.setCurrentWidget(self.page_sec3_compromise)
            else:
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
        """Smart focus: automatically focus the most appropriate field depending on section."""
        if not self.isVisible():
            return
        if self.form_section == 0:
            if not self.txt_case_black.text().strip():
                self.txt_case_black.setFocus()
                self.txt_case_black.selectAll()
            elif not self.txt_case_type.text().strip():
                self.txt_case_type.setFocus()
            elif not self.txt_judge1.text().strip():
                self.txt_judge1.setFocus()
            else:
                self.txt_case_black.setFocus()
        elif self.form_section == 1:
            if getattr(self, 'doc_type', 'report') == 'compromise':
                if hasattr(self, 'txt_compromise_subject') and not self.txt_compromise_subject.text().strip():
                    self.txt_compromise_subject.setFocus()
                elif hasattr(self, 'txt_compromise_date') and not self.txt_compromise_date.text().strip():
                    self.txt_compromise_date.setFocus()
                elif hasattr(self, 'txt_refund_total') and not self.txt_refund_total.text().strip():
                    self.txt_refund_total.setFocus()
            else:
                if hasattr(self, 'signatories_widget'):
                    self.signatories_widget.setFocus()
        elif self.form_section == 2:
            if getattr(self, 'doc_type', 'report') == 'compromise':
                if hasattr(self, 'btn_generate_compromise'):
                    self.btn_generate_compromise.setFocus()
            else:
                if self.paragraph_cards:
                    card0 = self.paragraph_cards[0]
                    if hasattr(card0, 'txt_editor'):
                        card0.txt_editor.setFocus()
                    elif hasattr(card0, 'txt_content'):
                        card0.txt_content.setFocus()
                elif hasattr(self, 'btn_generate'):
                    self.btn_generate.setFocus()

    def fill_compromise_date_from_excel(self):
        d = self.txt_day.text().strip()
        m = self.txt_month.text().strip()
        y = self.txt_year.text().strip()
        if not (d or m or y):
            QMessageBox.information(self, "แจ้งเตือน", "ไม่พบข้อมูลวันที่ในฟอร์ม กรุณาระบุในแท็บ 'ข้อมูลคดี & องค์คณะ'")
            return
        full_y = to_full_buddhist_year(y) if y else ""
        parts = [p for p in [d, m, full_y] if p]
        self.txt_compromise_date.setText(" ".join(parts))

    def fill_compromise_date_today(self):
        now = datetime.now()
        d_val = str(now.day)
        m_val = THAI_MONTHS[now.month - 1] if 1 <= now.month <= 12 else ""
        y_val = str(now.year + 543)
        parts = [p for p in [d_val, m_val, y_val] if p]
        self.txt_compromise_date.setText(" ".join(parts))

    @staticmethod
    def format_thai_currency(text: str) -> str:
        """Format number string with Thai comma thousands separators, supporting both Arabic and Thai numerals."""
        if not text:
            return ""
        has_dot = '.' in text
        parts = text.split('.', 1)
        int_part = parts[0]
        dec_part = parts[1] if has_dot else ""

        clean_int = re.sub(r'[^0-9\u0e50-\u0e59]', '', int_part)
        if not clean_int:
            if has_dot:
                clean_dec = re.sub(r'[^0-9\u0e50-\u0e59]', '', dec_part)[:2]
                return f".{clean_dec}"
            return ""

        reversed_digits = clean_int[::-1]
        chunks = [reversed_digits[i:i+3] for i in range(0, len(reversed_digits), 3)]
        formatted_int = ','.join(chunks)[::-1]

        if has_dot:
            clean_dec = re.sub(r'[^0-9\u0e50-\u0e59]', '', dec_part)[:2]
            return f"{formatted_int}.{clean_dec}"
        return formatted_int

    def handle_refund_total_edited(self, raw_text: str):
        """Auto-formats currency with commas as the user types, preserving cursor position."""
        cursor_pos = self.txt_refund_total.cursorPosition()
        chars_before = raw_text[:cursor_pos]
        significant_before = len(re.findall(r'[0-9\u0e50-\u0e59.]', chars_before))

        formatted = self.format_thai_currency(raw_text)
        if formatted != raw_text:
            self.txt_refund_total.blockSignals(True)
            self.txt_refund_total.setText(formatted)
            self.txt_refund_total.blockSignals(False)

            if significant_before == 0:
                new_cursor = 0
            else:
                count = 0
                new_cursor = len(formatted)
                for idx, ch in enumerate(formatted):
                    if ch in '0123456789๐๑๒๓๔๕๖๗๘๙.':
                        count += 1
                    if count == significant_before:
                        new_cursor = idx + 1
                        break
            self.txt_refund_total.setCursorPosition(new_cursor)

    def convert_refund_to_thai_digits(self):
        val = self.txt_refund_total.text().strip()
        if not val:
            return
        arabic_to_thai = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")
        thai_to_arabic = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")

        has_arabic = any(c in "0123456789" for c in val)
        if has_arabic:
            new_val = val.translate(arabic_to_thai)
        else:
            new_val = val.translate(thai_to_arabic)

        formatted = self.format_thai_currency(new_val)
        self.txt_refund_total.setText(formatted)

    def update_compromise_summary(self):
        default_court = storage_service.get_default_court_name()
        if not self.txt_court_name.text().strip() and default_court:
            self.txt_court_name.setText(default_court)

        black = self.txt_case_black.text().strip() or "-"
        red = self.txt_case_red.text().strip() or "-"
        court = self.txt_court_name.text().strip() or default_court or "-"
        court_display = court if (court.startswith("ศาล") or court == "-") else f"ศาล{court}"
        d = self.txt_day.text().strip() or "-"
        m = self.txt_month.text().strip() or "-"
        y = self.txt_year.text().strip() or "-"
        c_type = self.txt_case_type.text().strip() or "-"
        subj = self.txt_compromise_subject.text().strip() if hasattr(self, 'txt_compromise_subject') else "-"
        subj = subj or "(ยังไม่ระบุ)"
        plaintiff = self.txt_plaintiff.text().strip() or "-"
        defendant = self.txt_defendant.text().strip() or "-"
        c_date = self.txt_compromise_date.text().strip() if hasattr(self, 'txt_compromise_date') else "-"
        c_date = c_date or "(ยังไม่ระบุ)"
        refund = self.txt_refund_total.text().strip() if hasattr(self, 'txt_refund_total') else "-"
        refund = refund or "(ยังไม่ระบุ)"
        j1 = self.cmb_judge1.currentText().strip() or "-"
        j2 = self.txt_judge2.text().strip() or "(ไม่มีองค์คณะคนที่ ๒)"

        summary_html = f"""
        <b>ข้อมูลคดี:</b> คดีหมายเลขดำที่ <b>{black}</b> &nbsp;|&nbsp; คดีหมายเลขแดงที่ <b>{red}</b><br/>
        <b>ศาล:</b> {court_display} &nbsp;|&nbsp; <b>ความ:</b> {c_type}<br/>
        <b>วันที่ในเอกสาร:</b> วันที่ {d} เดือน {m} พุทธศักราช {y}<br/>
        <b>คู่ความ:</b> โจทก์: <b>{plaintiff}</b> &nbsp;|&nbsp; จำเลย: <b>{defendant}</b><br/>
        <b>เรื่อง (ข้อหาแห่งคดี):</b> <span style='color: #1e3a8a; font-weight: bold;'>{subj}</span><br/>
        <b>สัญญาประนีประนอมยอมความ:</b> ฉบับลงวันที่ <b>{c_date}</b><br/>
        <b>คืนค่าขึ้นศาลเป็นกรณีพิเศษ:</b> <span style='color: #16a34a; font-weight: bold;'>{refund} บาท</span><br/>
        <b>องค์คณะผู้พิพากษา:</b> เจ้าของสำนวน: {j1} &nbsp;|&nbsp; องค์คณะ: {j2}
        """
        if hasattr(self, 'lbl_comp_summary_text'):
            self.lbl_comp_summary_text.setText(summary_html)

    def _create_dynamic_fields_widget(self):
        """Creates a styled card container for dynamically detected custom template variables."""
        frame = QFrame()
        frame.setObjectName("innerGroupFrame")
        frame.setStyleSheet("""
            QFrame#innerGroupFrame {
                background-color: #ffffff;
                border: 1px solid #fed7aa;
                border-left: 5px solid #f59e0b;
                border-radius: 8px;
            }
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(20, 18, 20, 20)
        lay.setSpacing(12)

        h_head = QHBoxLayout()
        h_head.setSpacing(10)
        lbl_ico = QLabel()
        lbl_ico.setPixmap(get_pixmap("file-text", color="#d97706", size=22))
        h_head.addWidget(lbl_ico)

        v_t = QVBoxLayout()
        v_t.setSpacing(3)
        frame.lbl_title = QLabel("ช่องกรอกข้อมูลเพิ่มเติมสำหรับตัวแปรใน Template")
        frame.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #92400e;")
        frame.lbl_desc = QLabel("ตรวจพบตัวแปรที่ท่านระบุไว้ในแม่แบบ กรุณากรอกข้อมูลในช่องด้านล่างเพื่อนำไปแทรกลงในเอกสาร")
        frame.lbl_desc.setStyleSheet("font-size: 13px; color: #b45309;")
        v_t.addWidget(frame.lbl_title)
        v_t.addWidget(frame.lbl_desc)
        h_head.addLayout(v_t)
        h_head.addStretch()

        btn_apply = QPushButton("แทนที่ลงในข้อความย่อหน้าทันที")
        btn_apply.setObjectName("secondaryButtonSmall")
        btn_apply.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        btn_apply.setIcon(get_icon("check", color="#4c1d95", size=14))
        btn_apply.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1px solid #d8b4fe; border-radius: 5px; padding: 4px 10px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #e9d5ff; border-color: #c084fc; }"
        )
        btn_apply.setToolTip("นำข้อความที่กรอกไปแทนที่ใน {{ตัวแปร}} ในกล่องข้อความย่อหน้าทันที")
        btn_apply.clicked.connect(self.apply_dynamic_values_to_paragraph_cards)
        h_head.addWidget(btn_apply)

        lay.addLayout(h_head)

        lbl_dyn_tip = QLabel(
            "<b>คำแนะนำ:</b> ตัวแปรที่ตั้งไว้ในรูปแบบ <code>{{ชื่อตัวแปร}}</code> ใน Template หรือย่อหน้า "
            "จะถูกสร้างเป็นช่องกรอกข้อมูลด้านล่างนี้โดยอัตโนมัติ พร้อมแสดงชื่อตัวแปรเป็นหัวข้อกำกับ (Label) "
            "ท่านสามารถกรอกข้อมูลแล้วกด <b>แทนที่ลงในข้อความย่อหน้าทันที</b> หรือกดส่งออก Word "
            "ระบบจะนำข้อความที่กรอกไปแทนที่ในเอกสารทันที"
        )
        lbl_dyn_tip.setTextFormat(Qt.TextFormat.RichText)
        lbl_dyn_tip.setWordWrap(True)
        lbl_dyn_tip.setStyleSheet("font-size: 12.5px; color: #78350f; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 6px 12px;")
        lay.addWidget(lbl_dyn_tip)

        inputs_box = QVBoxLayout()
        inputs_box.setSpacing(10)
        lay.addLayout(inputs_box)
        frame.setVisible(False)
        return frame, inputs_box

    def apply_dynamic_values_to_paragraph_cards(self):
        """Quickly replace {{var}} directly inside paragraph card textboxes with current input values."""
        if not self.dynamic_inputs:
            return
        replacements = {var: edt.text().strip() for var, edt in self.dynamic_inputs.items() if edt.text().strip()}
        if not replacements:
            QMessageBox.information(self, "แจ้งเตือน", "กรุณากรอกข้อมูลในช่องตัวแปรก่อนกดแทนที่ข้อความ")
            return

        count_modified = 0
        for card in self.paragraph_cards:
            text = card.get_text()
            original = text
            for var, val in replacements.items():
                text = re.sub(r'\{\{\s*' + re.escape(var) + r'\s*\}\}', val, text)
                text = re.sub(r'\{\s*' + re.escape(var) + r'\s*\}', val, text)
            if text != original:
                card.set_text(text)
                count_modified += 1

        QMessageBox.information(
            self, "แทนที่ข้อความสำเร็จ",
            f"นำข้อมูลตัวแปรไปแทนที่ในข้อความย่อหน้าเรียบร้อยแล้ว ({count_modified} ย่อหน้า)"
        )

    def get_active_template_path(self) -> Optional[str]:
        """Resolve absolute path to currently active Word template based on document type."""
        tpl_dir = storage_service.get_templates_dir()
        if not tpl_dir or not os.path.exists(tpl_dir):
            return None

        is_compromise = (getattr(self, 'doc_type', 'report') == 'compromise')
        if is_compromise:
            candidates = ["คำพิพากษาตามยอม.docx", "template2.docx"]
        else:
            candidates = ["template.docx"]

        for c in candidates:
            p = os.path.join(tpl_dir, c)
            if os.path.exists(p):
                return p

        for f in os.listdir(tpl_dir):
            if f.endswith(".docx") and not f.startswith("~$"):
                if is_compromise and ("ตามยอม" in f or "template2" in f):
                    return os.path.join(tpl_dir, f)
                elif not is_compromise and "template" in f:
                    return os.path.join(tpl_dir, f)
        return None

    def scan_and_update_dynamic_fields(self):
        """
        Scan all paragraph cards and active Word template for custom {{variables}}.
        Dynamically generates labeled input fields with the variable name as the label.
        Automatically shows the container when variables exist, hides it when none exist.
        """
        is_compromise = (getattr(self, 'doc_type', 'report') == 'compromise')
        active_frame = getattr(self, 'group_dyn_fields_comp', None) if is_compromise else getattr(self, 'group_dyn_fields', None)
        inactive_frame = getattr(self, 'group_dyn_fields', None) if is_compromise else getattr(self, 'group_dyn_fields_comp', None)
        active_container = getattr(self, 'dyn_inputs_container_comp', None) if is_compromise else getattr(self, 'dyn_inputs_container', None)

        if inactive_frame:
            inactive_frame.setVisible(False)

        if not active_frame or not active_container:
            return

        # 1. Extract variables from all paragraph cards
        card_vars = set()
        for card in getattr(self, 'paragraph_cards', []):
            txt = card.get_text() if hasattr(card, 'get_text') else ""
            if txt:
                matches = re.findall(r'\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', txt)
                for m1, m2 in matches:
                    tag = (m1 or m2).strip()
                    clean_tag = tag.lstrip('#/').strip()
                    if clean_tag and clean_tag not in FORBIDDEN_CONTROL_KEYWORDS and not clean_tag.startswith(('#', '/')):
                        valid, _ = validate_template_variable(clean_tag)
                        if valid:
                            card_vars.add(clean_tag)

        # 2. Extract variables from active Word template
        tpl_path = self.get_active_template_path()
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
            active_frame.setVisible(False)
            self.dynamic_inputs.clear()
            return

        # 5. Preserve existing typed text
        current_values = {var: edt.text() for var, edt in self.dynamic_inputs.items()}

        # 6. Check if current inputs already match sorted_vars to avoid re-creating layout needlessly
        sorted_vars = sorted(list(custom_vars))
        existing_keys = sorted(list(self.dynamic_inputs.keys()))
        if existing_keys == sorted_vars:
            # Already matches exact keys, ensure frame is visible
            active_frame.setVisible(True)
            return

        # 7. Clear existing dynamic fields from container
        while active_container.count():
            item = active_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub_it = item.layout().takeAt(0)
                    if sub_it.widget():
                        sub_it.widget().deleteLater()

        self.dynamic_inputs.clear()

        # Update title text
        title_lbl = getattr(active_frame, 'lbl_title', None)
        if title_lbl:
            title_lbl.setText(f"ช่องกรอกข้อมูลเพิ่มเติมสำหรับตัวแปรใน Template (ตรวจพบ {len(sorted_vars)} รายการ)")

        # 8. Create labeled inputs for each variable (extracting field name as label)
        for var_name in sorted_vars:
            row = QHBoxLayout()
            row.setSpacing(14)

            # Field Name Label (ดึงชื่อ field มาแสดงเป็น label)
            lbl = QLabel(f"{var_name} :")
            lbl.setObjectName("fieldLabel")
            lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e3a8a; min-width: 140px;")
            row.addWidget(lbl)

            txt_input = QLineEdit()
            txt_input.setObjectName("formInput")
            txt_input.setPlaceholderText(f"กรอกข้อมูลสำหรับ \"{var_name}\"...")
            txt_input.setStyleSheet("""
                QLineEdit {
                    font-size: 14px;
                    padding: 8px 12px;
                    border: 1.5px solid #cbd5e1;
                    border-radius: 6px;
                    background: #ffffff;
                    color: #0f172a;
                }
                QLineEdit:focus {
                    border: 2px solid #2563eb;
                    background: #eff6ff;
                }
            """)
            if var_name in current_values:
                txt_input.setText(current_values[var_name])
            row.addWidget(txt_input, 1)

            active_container.addLayout(row)
            self.dynamic_inputs[var_name] = txt_input

        active_frame.setVisible(True)

    def create_form_field(self, layout, label_text: str, default_val: str, widget=None) -> QLineEdit:
        box = QVBoxLayout()
        box.setSpacing(5)
        lbl = QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        txt = widget if widget is not None else QLineEdit()
        if hasattr(txt, "setText") and default_val:
            txt.setText(default_val)
        box.addWidget(lbl)
        box.addWidget(txt)
        layout.addLayout(box)
        return txt

    def update_case_types(self, new_types: List[str]):
        self.case_types_list = list(new_types)
        if hasattr(self, 'txt_case_type'):
            self.txt_case_type.set_items(self.case_types_list)

    def load_case_row(self, row: Dict[str, Any], mapping: Dict[str, str]):
        """Populate form fields with selected row data and guessed column mapping."""
        black_col = mapping.get('case_black_no')
        self.txt_case_black.setText(str(row.get(black_col, '')).strip() if (black_col and black_col in row and row[black_col] is not None) else "")

        red_col = mapping.get('case_red_no')
        self.txt_case_red.setText(str(row.get(red_col, '')).strip() if (red_col and red_col in row and row[red_col] is not None) else "")

        type_col = mapping.get('case_type')
        type_val = str(row.get(type_col, '')).strip() if (type_col and type_col in row and row[type_col] is not None) else ""
        self.txt_case_type.setText(type_val if type_val else "แพ่ง")

        purpose_col = mapping.get('hearing_purpose') or mapping.get('appointment_date')
        self.txt_hearing_purpose.setText(str(row.get(purpose_col, '')).strip() if (purpose_col and purpose_col in row and row[purpose_col] is not None) else "")

        court_col = mapping.get('court_name')
        excel_court = str(row.get(court_col, '')).strip() if (court_col and court_col in row and row[court_col] is not None) else ""
        default_court = storage_service.get_default_court_name()

        # Sanitize and validate whether excel_court is really a legitimate court institution name
        invalid_court_indicators = ['มาศาล', 'ไม่มา', 'คำสั่ง', 'เลื่อน', 'รอนัด', 'ส่งหมาย', 'เจ้าหน้าที่', '-', 'none', 'nan', 'null']
        is_genuine_court = False
        if excel_court:
            c_lower = excel_court.lower()
            if c_lower not in invalid_court_indicators and not any(ind == c_lower for ind in invalid_court_indicators):
                if excel_court.startswith("ศาล") and not any(kw in excel_court for kw in ['มาศาล', 'คำสั่งศาล', 'หมายศาล']):
                    is_genuine_court = True

        if is_genuine_court:
            self.txt_court_name.setText(excel_court)
        elif default_court:
            self.txt_court_name.setText(default_court)
        else:
            self.txt_court_name.setText(excel_court if excel_court.startswith("ศาล") else "")

        plaintiff_col = mapping.get('plaintiff_name')
        self.txt_plaintiff.setText(str(row.get(plaintiff_col, '')).strip() if (plaintiff_col and plaintiff_col in row and row[plaintiff_col] is not None) else "")

        def_col = mapping.get('defendant_name')
        self.txt_defendant.setText(str(row.get(def_col, '')).strip() if (def_col and def_col in row and row[def_col] is not None) else "")

        time_col = mapping.get('hearing_time')
        self.txt_time.setText(str(row.get(time_col, '')).strip() if (time_col and time_col in row and row[time_col] is not None) else "")

        # Date mapping
        date_col = mapping.get('hearing_date')
        day_col = mapping.get('hearing_day')
        month_col = mapping.get('hearing_month')
        year_col = mapping.get('hearing_year')

        d, m, y = '', '', ''
        if date_col and date_col in row and row[date_col]:
            d, m, y = format_thai_date(row[date_col])
        if day_col and day_col in row and row[day_col]:
            d = str(row[day_col]).strip()
        if month_col and month_col in row and row[month_col]:
            m = str(row[month_col]).strip()
        if year_col and year_col in row and row[year_col]:
            y = to_full_buddhist_year(row[year_col])

        self.txt_day.setText(d)
        self.txt_month.setText(m)
        self.txt_year.setText(to_full_buddhist_year(y) if y else "")

        # Auto-suggest formatted compromise date if empty (e.g. 17 กันยายน 2569)
        if hasattr(self, 'txt_compromise_date') and not self.txt_compromise_date.text().strip():
            if d and m and y:
                full_y = to_full_buddhist_year(y) if y else ""
                parts = [p for p in [d, m, full_y] if p]
                self.txt_compromise_date.setText(" ".join(parts))

        # Check if row has subject/matter column
        subj_col = mapping.get('case_subject') or mapping.get('เรื่อง')
        if not subj_col:
            for c in row.keys():
                if 'เรื่อง' in c or 'ข้อหา' in c:
                    subj_col = c
                    break
        if subj_col and hasattr(self, 'txt_compromise_subject'):
            v_subj = str(row.get(subj_col, '')).strip() if row.get(subj_col) is not None else ""
            self.txt_compromise_subject.setText(v_subj)

        # Judges mapping
        judge1_col = mapping.get('judge_1_name') or mapping.get('judge_name')
        judge2_col = mapping.get('judge_2_name')

        judge1_val = str(row.get(judge1_col, '')).strip() if (judge1_col and judge1_col in row and row[judge1_col] is not None) else ""
        judge2_val = str(row.get(judge2_col, '')).strip() if (judge2_col and judge2_col in row and row[judge2_col] is not None) else ""

        self.cmb_judge1.setEditText(judge1_val)

        if judge2_val:
            self.txt_judge2.setText(judge2_val)
            self.update_bench_status(f"ข้อมูลองค์คณะจากตาราง Excel: '{judge2_val}'", "font-size: 13px; color: #16a34a; font-weight: 600;")
        else:
            self.txt_judge2.clear()
            if judge1_val:
                paired = storage_service.find_paired_judge(judge1_val)
                if paired:
                    self.update_bench_status(f"ตรวจพบคู่องค์คณะในฐานข้อมูล: '{paired}' (จะถามยืนยันเมื่อไปขั้นตอนถัดไป)", "font-size: 13px; color: #2563eb; font-weight: 600;")
                else:
                    self.update_bench_status("ยังไม่มีการจับคู่สำหรับผู้พิพากษาท่านนี้", "font-size: 13px; color: #64748b;")
            else:
                self.update_bench_status("")

    def update_bench_status(self, text: str, style: str = ""):
        self.lbl_bench_status.setText(text)
        if style:
            self.lbl_bench_status.setStyleSheet(style)
        self.lbl_bench_status.setVisible(bool(text))

    def confirm_bench_pair_if_needed(self):
        judge1_val = self.cmb_judge1.currentText().strip()
        judge2_val = self.txt_judge2.text().strip()

        if not judge2_val and judge1_val:
            paired = storage_service.find_paired_judge(judge1_val)
            if paired:
                reply = QMessageBox.question(
                    self, "ตรวจพบคู่องค์คณะผู้พิพากษา",
                    f"ในตารางระบุผู้พิพากษาเจ้าของสำนวน คือ '{judge1_val}'\n"
                    f"ตรวจพบว่ามีการจับคู่กับ '{paired}' ไว้ในฐานข้อมูลระบบ\n\n"
                    f"ต้องการเติมชื่อผู้พิพากษาองค์คณะให้อัตโนมัติหรือไม่?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.txt_judge2.setText(paired)
                    self.update_bench_status(f"เติมชื่อองค์คณะที่จับคู่ไว้: '{paired}'", "font-size: 13px; color: #16a34a; font-weight: 600;")
                else:
                    self.txt_judge2.clear()
                    self.update_bench_status("คงเป็นค่าว่างตามที่เลือก", "font-size: 13px; color: #64748b;")
            else:
                self.txt_judge2.clear()
                self.update_bench_status("ไม่พบคู่องค์คณะในฐานข้อมูล (คงเป็นค่าว่างไว้ก่อน)", "font-size: 13px; color: #64748b;")

        if not self.txt_court_name.text().strip():
            self.txt_court_name.setText(storage_service.get_default_court_name())

    def handle_next_to_attendees(self):
        case_black = self.txt_case_black.text().strip()
        if not case_black:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุคดีหมายเลขดำที่ในแบบฟอร์ม")
            self.set_form_section(0)
            self.txt_case_black.setFocus()
            return

        j1_val = self.cmb_judge1.currentText().strip()
        j2_val = self.txt_judge2.text().strip()
        if not j2_val and j1_val:
            paired = storage_service.find_paired_judge(j1_val)
            if paired:
                reply = QMessageBox.question(
                    self, "ตรวจพบคู่องค์คณะผู้พิพากษา",
                    f"ในตารางระบุผู้พิพากษาเจ้าของสำนวน คือ '{j1_val}'\n"
                    f"ตรวจพบว่ามีการจับคู่กับ '{paired}' ไว้ในฐานข้อมูลระบบ\n\n"
                    f"ต้องการเติมชื่อผู้พิพากษาองค์คณะให้อัตโนมัติหรือไม่?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.txt_judge2.setText(paired)
                    self.lbl_bench_status.setText(f"เติมชื่อองค์คณะที่จับคู่ไว้: '{paired}'")
                    self.lbl_bench_status.setStyleSheet("font-size: 13px; color: #16a34a; font-weight: 600;")
        self.set_form_section(1)

    # -------------------------------------------------------------------------
    # Bench Pairing Logic
    # -------------------------------------------------------------------------
    def refresh_judge1_completer(self):
        pairs = storage_service.load_bench_pairs()
        current_j1 = self.txt_judge1.text() if hasattr(self, 'txt_judge1') else ""
        current_j2 = self.txt_judge2.text() if hasattr(self, 'txt_judge2') else ""

        if not hasattr(self, 'txt_judge1'):
            return

        judge1_names = []
        judge2_names = []
        for p in pairs:
            j1 = p.get("judge1", "").strip()
            j2 = p.get("judge2", "").strip()
            if j1 and j1 not in judge1_names:
                judge1_names.append(j1)
            if j2 and j2 not in judge2_names:
                judge2_names.append(j2)

        self.txt_judge1.set_items(judge1_names)
        if hasattr(self, 'txt_judge2'):
            self.txt_judge2.set_items(judge2_names)

        if current_j1:
            self.txt_judge1.setText(current_j1)
        if current_j2:
            self.txt_judge2.setText(current_j2)

    def handle_judge1_changed(self, text: str):
        j1_clean = text.strip()
        if not j1_clean:
            self.update_bench_status("")
            return

        paired_j2 = storage_service.find_paired_judge(j1_clean)
        if paired_j2:
            self.txt_judge2.setText(paired_j2)
            self.update_bench_status(f"ตรวจพบองค์คณะที่จับคู่ไว้: '{paired_j2}'", "font-size: 13px; color: #16a34a; font-weight: 600;")
        else:
            self.update_bench_status("ยังไม่มีการจับคู่สำหรับผู้พิพากษาท่านนี้ (พิมพ์ชื่อองค์คณะแล้วกดปุ่ม 'บันทึกการจับคู่นี้' ได้)", "font-size: 13px; color: #64748b;")

    def handle_save_current_pairing(self):
        j1 = self.cmb_judge1.currentText().strip()
        j2 = self.txt_judge2.text().strip()
        if not j1:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อผู้พิพากษาเจ้าของสำนวน")
            return
        if not j2:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อผู้พิพากษาองค์คณะ")
            return

        storage_service.save_or_update_pair(j1, j2)
        self.refresh_judge1_completer()
        self.cmb_judge1.setEditText(j1)
        self.update_bench_status(f"บันทึกการจับคู่ระหว่าง '{j1}' และ '{j2}' เรียบร้อยแล้ว", "font-size: 13px; color: #16a34a; font-weight: 600;")
        QMessageBox.information(
            self, "บันทึกสำเร็จ",
            f"บันทึกการจับคู่องค์คณะเรียบร้อยแล้ว:\n- ผู้พิพากษาเจ้าของสำนวน: {j1}\n- ผู้พิพากษาองค์คณะ: {j2}\n\nระบบจะจำค่านี้ไว้ทุกครั้งที่เปิดโปรแกรม"
        )

    def save_current_court_as_default(self):
        c = self.txt_court_name.text().strip()
        if not c:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อศาลในช่องข้อความก่อนกดบันทึก")
            self.txt_court_name.setFocus()
            return
        storage_service.set_default_court_name(c)
        self.court_saved_as_default.emit(c)
        QMessageBox.information(
            self, "บันทึกสำเร็จ",
            f"บันทึก '{c}' เป็นชื่อศาลเริ่มต้นเรียบร้อยแล้ว\nระบบจะนำชื่อนี้มาแสดงในแบบฟอร์มให้อัตโนมัติทุกครั้ง"
        )

    def refresh_default_court(self):
        """Force refresh the court name from storage if empty or requested."""
        c = storage_service.get_default_court_name()
        if c:
            self.txt_court_name.setText(c)

    # -------------------------------------------------------------------------
    # Paragraphs Dynamic Management
    # -------------------------------------------------------------------------
    def add_paragraph_card(self, initial_text: str = "") -> ParagraphCard:
        idx = len(self.paragraph_cards) + 1
        card = ParagraphCard(index=idx, text=initial_text, parent=self)
        card.move_up_requested.connect(self.move_paragraph_up)
        card.move_down_requested.connect(self.move_paragraph_down)
        card.delete_requested.connect(self.delete_paragraph_card)
        card.reorder_requested.connect(self.reorder_paragraph_cards)
        card.text_changed.connect(self.scan_and_update_dynamic_fields)

        self.paragraph_cards.append(card)
        self.para_cards_container.addWidget(card)
        if hasattr(self, 'para_placeholder'):
            self.para_placeholder.setVisible(False)
        if hasattr(self, 'btn_bottom_add_para'):
            self.btn_bottom_add_para.setVisible(True)
        if hasattr(self, 'btn_bottom_add_tpl'):
            self.btn_bottom_add_tpl.setVisible(True)
        self.refresh_paragraph_indices()
        self.scan_and_update_dynamic_fields()
        return card

    def reorder_paragraph_cards(self, src_idx: int, target_idx: int):
        s = src_idx - 1
        t = target_idx - 1
        if 0 <= s < len(self.paragraph_cards) and 0 <= t < len(self.paragraph_cards):
            card = self.paragraph_cards.pop(s)
            self.paragraph_cards.insert(t, card)
            self.rebuild_paragraph_layout()

    def handle_add_paragraph_from_template(self):
        dlg = TemplateSelectDialog(self)
        if dlg.exec() and dlg.selected_content:
            self.add_paragraph_card(dlg.selected_content)

    def move_paragraph_up(self, card: ParagraphCard):
        try:
            idx = self.paragraph_cards.index(card)
            if idx > 0:
                self.paragraph_cards[idx], self.paragraph_cards[idx - 1] = self.paragraph_cards[idx - 1], self.paragraph_cards[idx]
                self.rebuild_paragraph_layout()
        except ValueError:
            pass

    def move_paragraph_down(self, card: ParagraphCard):
        try:
            idx = self.paragraph_cards.index(card)
            if idx < len(self.paragraph_cards) - 1:
                self.paragraph_cards[idx], self.paragraph_cards[idx + 1] = self.paragraph_cards[idx + 1], self.paragraph_cards[idx]
                self.rebuild_paragraph_layout()
        except ValueError:
            pass

    def delete_paragraph_card(self, card: ParagraphCard):
        try:
            self.paragraph_cards.remove(card)
            self.para_cards_container.removeWidget(card)
            card.deleteLater()

            if not self.paragraph_cards:
                if hasattr(self, 'para_placeholder'):
                    self.para_placeholder.setVisible(True)
                if hasattr(self, 'btn_bottom_add_para'):
                    self.btn_bottom_add_para.setVisible(False)
                if hasattr(self, 'btn_bottom_add_tpl'):
                    self.btn_bottom_add_tpl.setVisible(False)
                self.lbl_para_count.setText("(ไม่มีการระบุย่อหน้าเพิ่มเติม)")
            else:
                self.refresh_paragraph_indices()
            self.scan_and_update_dynamic_fields()
        except ValueError:
            pass

    def rebuild_paragraph_layout(self):
        for card in self.paragraph_cards:
            self.para_cards_container.removeWidget(card)
        for card in self.paragraph_cards:
            self.para_cards_container.addWidget(card)
        self.refresh_paragraph_indices()

    def refresh_paragraph_indices(self):
        total = len(self.paragraph_cards)
        if total == 0:
            self.lbl_para_count.setText("(ไม่มีการระบุย่อหน้าเพิ่มเติม)")
        else:
            self.lbl_para_count.setText(f"(ทั้งหมด {total} ย่อหน้า)")
        for i, card in enumerate(self.paragraph_cards, start=1):
            card.set_index(i, is_first=(i == 1), is_last=(i == total))

    # -------------------------------------------------------------------------
    # Word Document Generator
    # -------------------------------------------------------------------------
    def handle_generate_docx(self):
        case_black = self.txt_case_black.text().strip()
        if not case_black:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุคดีหมายเลขดำที่ในแบบฟอร์ม")
            self.set_form_section(0)
            self.txt_case_black.setFocus()
            return

        tpl_dir = storage_service.get_templates_dir()

        tpl_candidates = ["template.docx"]
        tpl_path = None

        for c in tpl_candidates:
            p = os.path.join(tpl_dir, c)
            if os.path.exists(p):
                tpl_path = p
                break

        if not tpl_path and os.path.exists(tpl_dir):
            for f in os.listdir(tpl_dir):
                if f.endswith(".docx") and not f.startswith("~$"):
                    tpl_path = os.path.join(tpl_dir, f)
                    break

        if not tpl_path or not os.path.exists(tpl_path):
            QMessageBox.critical(self, "ข้อผิดพลาด", f"ไม่พบไฟล์ Template Word (.docx) ในโฟลเดอร์:\n{tpl_dir}")
            return

        safe_black = case_black.replace('/', '-').replace('\\', '-')
        default_filename = f"รายงาน_{safe_black}.docx"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "บันทึกรายงานกระบวนพิจารณา (.docx)", default_filename, "Word Document (*.docx)"
        )
        if not save_path:
            return

        # Collect dynamic template variables entered by user
        dyn_replacements = {var: edt.text().strip() for var, edt in self.dynamic_inputs.items()}

        raw_paragraphs = []
        for card in self.paragraph_cards:
            txt = card.get_text()
            if not txt:
                continue
            for var_name, val in dyn_replacements.items():
                if val:
                    txt = re.sub(r'\{\{\s*' + re.escape(var_name) + r'\s*\}\}', val, txt)
                    txt = re.sub(r'\{\s*' + re.escape(var_name) + r'\s*\}', val, txt)
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
            'judge_1_name': self.cmb_judge1.currentText().strip(),
            'judge_2_name': self.txt_judge2.text().strip(),
            'signatories': [{'position': pos} for pos in signatories],
            'attendees_summary': format_attendees_summary(signatories),
            'paragraphs': raw_paragraphs,
        }

        # Inject custom variables from template dynamic inputs
        for var_name, val in dyn_replacements.items():
            data[var_name] = val

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
                        subprocess.Popen(f'explorer /select,"{norm_file}"')
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

        subject = self.txt_compromise_subject.text().strip() if hasattr(self, 'txt_compromise_subject') else ""
        if not subject:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุ 'เรื่อง (ข้อหาแห่งคดี)' ซึ่งจำเป็นต้องใช้ในคำพิพากษาตามยอม")
            self.set_form_section(1)
            if hasattr(self, 'txt_compromise_subject'):
                self.txt_compromise_subject.setFocus()
            return

        c_date = self.txt_compromise_date.text().strip() if hasattr(self, 'txt_compromise_date') else ""
        if not c_date:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุ 'ฉบับลงวันที่ (สัญญาประนีประนอมยอมความ)' ซึ่งจำเป็นต้องใช้ในคำพิพากษาตามยอม")
            self.set_form_section(1)
            if hasattr(self, 'txt_compromise_date'):
                self.txt_compromise_date.setFocus()
            return

        refund = self.txt_refund_total.text().strip() if hasattr(self, 'txt_refund_total') else ""
        if not refund:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุ 'คืนค่าขึ้นศาลเป็นกรณีพิเศษ (บาท)' ซึ่งจำเป็นต้องใช้ในคำพิพากษาตามยอม")
            self.set_form_section(1)
            if hasattr(self, 'txt_refund_total'):
                self.txt_refund_total.setFocus()
            return

        refund = self.format_thai_currency(refund) or refund
        if hasattr(self, 'txt_refund_total'):
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

        safe_black = case_black.replace('/', '-').replace('\\', '-')
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
            'judge_1_name': self.cmb_judge1.currentText().strip(),
            'judge_2_name': self.txt_judge2.text().strip(),
        }

        # Inject custom variables from template dynamic inputs
        for var_name, edt in self.dynamic_inputs.items():
            data[var_name] = edt.text().strip()

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
                        subprocess.Popen(f'explorer /select,"{norm_file}"')
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

