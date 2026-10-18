"""
Case Information Section Component.
Encapsulates case numbers, court name, case type, hearing purpose, date/time, and parties.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator

from constants import DEFAULT_CASE_TYPES
from services.excel_service import format_thai_date, to_full_buddhist_year, THAI_MONTHS
from services import storage_service
from services.icon_service import get_icon
from ui.components.autocomplete_input import JudicialAutocompleteInput

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


class CaseInfoSectionWidget(QWidget):
    """Component for Case Information & Appointment details."""

    court_saved_as_default = Signal(str)

    def __init__(self, case_types_list: Optional[List[str]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.case_types_list: List[str] = list(case_types_list) if case_types_list else list(DEFAULT_CASE_TYPES)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)

        group_case = QFrame()
        group_case.setObjectName("innerGroupFrame")
        group_case_layout = QVBoxLayout(group_case)
        group_case_layout.setContentsMargins(20, 18, 20, 20)
        group_case_layout.setSpacing(14)

        lbl_sec1 = QLabel("ข้อมูลคดีความและรายละเอียดนัดพิจารณา")
        lbl_sec1.setObjectName("sectionHeaderTitle")
        group_case_layout.addWidget(lbl_sec1)

        # Row 1: Black No, Red No, Court
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
        default_court = storage_service.get_default_court_name()
        if default_court:
            self.txt_court_name.setText(default_court)
        v_court.addWidget(self.txt_court_name)
        row1.addLayout(v_court)
        group_case_layout.addLayout(row1)

        # Row 1.5: Case Type and Hearing Purpose
        row_extra = QHBoxLayout()
        row_extra.setSpacing(14)
        self.txt_case_type = JudicialAutocompleteInput(items=self.case_types_list, placeholder="พิมพ์หรือเลือกประเภทคดี...")
        self.create_form_field(row_extra, "ประเภทคดี (ความ)", "", widget=self.txt_case_type)

        self.txt_hearing_purpose = JudicialAutocompleteInput(items=COMMON_HEARING_PURPOSES, placeholder="พิมพ์หรือเลือกเหตุที่นัด...")
        self.create_form_field(row_extra, "เหตุที่นัด", "", widget=self.txt_hearing_purpose)
        group_case_layout.addLayout(row_extra)

        # Row 2: Date and Time
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

        # Row 3: Parties
        row3 = QHBoxLayout()
        row3.setSpacing(14)
        self.txt_plaintiff = self.create_form_field(row3, "โจทก์ / ผู้ร้อง", "")
        self.txt_defendant = self.create_form_field(row3, "จำเลย / ผู้คัดค้าน", "")
        group_case_layout.addLayout(row3)

        main_layout.addWidget(group_case)

    def create_form_field(self, layout: QHBoxLayout, label_text: str, default_val: str, widget=None) -> QLineEdit:
        v_box = QVBoxLayout()
        v_box.setSpacing(5)
        lbl = QLabel(label_text)
        lbl.setObjectName("fieldLabel")
        v_box.addWidget(lbl)
        if widget is None:
            widget = QLineEdit(default_val)
        v_box.addWidget(widget)
        layout.addLayout(v_box)
        return widget

    def update_case_types(self, new_types: List[str]):
        self.case_types_list = list(new_types)
        if hasattr(self, 'txt_case_type'):
            self.txt_case_type.set_items(self.case_types_list)

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
        c = storage_service.get_default_court_name()
        if c:
            self.txt_court_name.setText(c)

    def load_case_row(self, row: Dict[str, Any], mapping: Dict[str, str]) -> Tuple[str, str, str]:
        """Populate form fields with selected row data and guessed column mapping."""
        black_col = mapping.get('case_black_no') or mapping.get('case_black')
        self.txt_case_black.setText(str(row.get(black_col, '')).strip() if (black_col and black_col in row and row[black_col] is not None) else "")

        red_col = mapping.get('case_red_no') or mapping.get('case_red')
        self.txt_case_red.setText(str(row.get(red_col, '')).strip() if (red_col and red_col in row and row[red_col] is not None) else "")

        type_col = mapping.get('case_type')
        type_val = str(row.get(type_col, '')).strip() if (type_col and type_col in row and row[type_col] is not None) else ""
        self.txt_case_type.setText(type_val if type_val else "แพ่ง")

        purpose_col = mapping.get('hearing_purpose') or mapping.get('appointment_date') or mapping.get('appointment_reason') or mapping.get('appointment_purpose') or mapping.get('นัดมาทำไม')
        self.txt_hearing_purpose.setText(str(row.get(purpose_col, '')).strip() if (purpose_col and purpose_col in row and row[purpose_col] is not None) else "")

        court_col = mapping.get('court_name') or mapping.get('court')
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

        plaintiff_col = mapping.get('plaintiff_name') or mapping.get('plaintiff')
        self.txt_plaintiff.setText(str(row.get(plaintiff_col, '')).strip() if (plaintiff_col and plaintiff_col in row and row[plaintiff_col] is not None) else "")

        def_col = mapping.get('defendant_name') or mapping.get('defendant')
        self.txt_defendant.setText(str(row.get(def_col, '')).strip() if (def_col and def_col in row and row[def_col] is not None) else "")

        time_col = mapping.get('hearing_time') or mapping.get('time')
        self.txt_time.setText(str(row.get(time_col, '')).strip() if (time_col and time_col in row and row[time_col] is not None) else "")

        # Date mapping
        date_col = mapping.get('hearing_date') or mapping.get('date')
        day_col = mapping.get('hearing_day')
        month_col = mapping.get('hearing_month')
        year_col = mapping.get('hearing_year')

        d, m, y = '', '', ''
        if date_col and date_col in row and row[date_col]:
            res = format_thai_date(row[date_col])
            if isinstance(res, (tuple, list)) and len(res) == 3:
                d, m, y = str(res[0] or ""), str(res[1] or ""), str(res[2] or "")
            elif isinstance(res, str):
                match = re.match(r"^(\d+)\s+([^\s\d]+)\s+(\d+)$", res.strip())
                if match:
                    d, m, y = match.group(1), match.group(2), match.group(3)
                else:
                    d = res.strip()
        if day_col and day_col in row and row[day_col]:
            d = str(row[day_col]).strip()
        if month_col and month_col in row and row[month_col]:
            m = str(row[month_col]).strip()
        if year_col and year_col in row and row[year_col]:
            y = to_full_buddhist_year(row[year_col])

        self.txt_day.setText(d)
        self.txt_month.setText(m)
        self.txt_year.setText(to_full_buddhist_year(y) if y else "")
        return d, m, y

    def get_case_data(self) -> Dict[str, str]:
        return {
            "case_black_no": self.txt_case_black.text().strip(),
            "case_red_no": self.txt_case_red.text().strip(),
            "court_name": self.txt_court_name.text().strip(),
            "case_type": self.txt_case_type.text().strip(),
            "hearing_purpose": self.txt_hearing_purpose.text().strip(),
            "day": self.txt_day.text().strip(),
            "month": self.txt_month.text().strip(),
            "year": self.txt_year.text().strip(),
            "hearing_time": self.txt_time.text().strip(),
            "plaintiff_name": self.txt_plaintiff.text().strip(),
            "defendant_name": self.txt_defendant.text().strip(),
        }

    def focus_first_empty_field(self):
        if not self.txt_case_black.text().strip():
            self.txt_case_black.setFocus()
            self.txt_case_black.selectAll()
        elif not self.txt_case_type.text().strip():
            self.txt_case_type.setFocus()
        else:
            self.txt_case_black.setFocus()
